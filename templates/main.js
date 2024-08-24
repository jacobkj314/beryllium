// Function to convert an epoch timestamp to the desired "YYYY/MM/DD HH:mm:ss" format
function epoch_timestamp_to_local_human_readable_timestamp(epochString) {

    console.log(epochString)

    // Convert the epoch string to a number
    const epoch = parseInt(epochString);
    console.log(epoch)

    // Create a Date object from the epoch
    const date = new Date(epoch);
    console.log(date)

    // Format the date into "YYYY/MM/DD HH:mm:ss"
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0'); // Month is 0-based, so +1
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');

    return `${year}/${month}/${day} ${hours}:${minutes}:${seconds}`;
}

// Function to iterate over the children of a new post element and convert timestamp spans
function convertTimestampsInPost(post_id) {
    postElement = document.getElementById(post_id)

    // Get all child elements inside the post element
    const children = postElement.getElementsByTagName('*');

    // Loop through each child
    for (let i = 0; i < children.length; i++) {
        const child = children[i];

        // Check if the child is a span and has the 'epoch-timestamp' class
        if (child.tagName === 'SPAN' && child.classList.contains('epoch-timestamp')) {
            // Get the current innerHTML (the epoch timestamp)
            const epochTimestamp = child.innerHTML;

            // Convert the epoch timestamp to a human-readable local time format
            const localTime = epoch_timestamp_to_local_human_readable_timestamp(epochTimestamp);

            // Update the span's content with the local time
            child.innerHTML = localTime;

            // Optionally, change the class of the span to 'local-timestamp' after conversion
            child.classList.remove('epoch-timestamp');
            child.classList.add('local-timestamp');
        }
    }
}











var socket = io();

//this allows the server to send posts to the client
socket.on('add_post', function(data) {
    poster = data.poster;
    post_number = data.post_number;
    new_post = data.new_post;

    poster_is_current_user = (poster == '{{ current_user.username }}');
    if(poster_is_current_user){
        document.getElementById('upload_container').innerHTML = '';
    }
    
    post_id = "post_" + poster + "_" + post_number
    if(! document.getElementById(post_id)){ //check whether this post already exists
        //insert post
        post_container = document.getElementById(poster_is_current_user ? "current_user_content" : "other_user_content");
        post_container.insertAdjacentHTML('afterbegin', new_post);
        //activate comment box
        (function(currentPoster, currentPostNumber) {
            document.getElementById("user_" + currentPoster + "_post_" + currentPostNumber + "_comment_form").onsubmit = function(event) {
                event.preventDefault();
                const comment_text = document.getElementById(currentPoster + "_" + currentPostNumber + "_comment_text").value;
                const xhr = new XMLHttpRequest();
                xhr.open('POST', '/comment/', true);
                xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
                xhr.onload = function(){};
                const data = 'poster=' + encodeURIComponent(currentPoster) + '&post_number=' + encodeURIComponent(currentPostNumber) + '&comment_text=' + encodeURIComponent(comment_text);
                xhr.send(data);
            };
        })(poster, post_number);
        convertTimestampsInPost(post_id)
    }
});

//this allows the server to send individual comments
socket.on('add_comment', function(data) {
    console.log(data.poster + ' ' + data.post_number)
    console.log(data.new_comment)
    comment_section_id = 'user_' + data.poster + '_post_' + data.post_number + '_comments';
    document.getElementById(comment_section_id).insertAdjacentHTML('beforeend', data.new_comment);
    convertTimestampsInPost(comment_section_id)
});