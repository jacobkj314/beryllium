// Function to convert an epoch timestamp to the desired "YYYY/MM/DD HH:mm:ss" format
function epoch_timestamp_to_local_human_readable_timestamp(epochString) {
    // Convert the epoch string to a number
    const epoch = parseInt(epochString);
    // Create a Date object from the epoch
    const date = new Date(epoch);
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

//this allows the server to send/remove posts to the client
socket.on('add_post', function(data) {
    poster = data.poster;
    post_number = data.post_number;
    new_post = data.new_post;
    timestamp = data.timestamp;

    poster_is_current_user = (poster == '{{ current_user.username }}');
    if(poster_is_current_user){
        document.getElementById('upload_container').innerHTML = '';
    }
    
    post_id = poster + "_" + post_number
    if(! document.getElementById(post_id)){ //check whether this post already exists
        //insert post
        post_container = document.getElementById(poster_is_current_user ? "current_user_content" : "other_user_content");
        post_container.insertAdjacentHTML('afterbegin', new_post);

        //activate comment box
        (function(currentPoster, currentPostNumber) {
            comment_form = document.getElementById(currentPoster + "_" + currentPostNumber + "_comment_form")
            comment_form.onsubmit = function(event) {
                event.preventDefault();
                comment_textbox = document.getElementById(currentPoster + "_" + currentPostNumber + "_comment_text")
                const comment_text = comment_textbox.value;
                const xhr = new XMLHttpRequest();
                xhr.open('POST', '/comment/', true);
                xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
                xhr.onload = function(){};
                const data = 'poster=' + encodeURIComponent(currentPoster) + '&post_number=' + encodeURIComponent(currentPostNumber) + '&comment_text=' + encodeURIComponent(comment_text);
                xhr.send(data);
                comment_textbox.value = ''
            };
        })(poster, post_number);
        //activate "delete post" form
        //TODO


        convertTimestampsInPost(post_id)
    }
});
socket.on('delete_post', function(data) {
    poster = data.poster;
    post_number = data.post_number;
    
    post_id = poster + "_" + post_number;
    post = document.getElementById(post_id);
    if(post){ //check whether this post already exists
        post.remove();
    }
});









//this allows the server to send/remove individual comments
socket.on('add_comment', function(data) {
    poster = data.poster;
    post_number = data.post_number;
    new_comment = data.new_comment;
    comment_number = data.comment_number;

    
    comment_section_id = poster + '_' + post_number + '_comments';
    comment_id = poster + '_' + post_number + '_' + comment_number;
    if(!document.getElementById(comment_id)){
        document.getElementById(comment_section_id).insertAdjacentHTML('beforeend', new_comment);
    }

    

    convertTimestampsInPost(comment_section_id);
    
    //activate "delete comment" button
    if(poster == '{{ current_user.username }}'){

        (function (current_poster, current_post_number, current_comment_number) {
            delete_button_id = current_poster + '_' + current_post_number + '_' + current_comment_number + "_delete";
            delete_button = document.getElementById(delete_button_id)
            delete_button.onclick = function(event){
                event.preventDefault();
                const xhr = new XMLHttpRequest();
                xhr.open('DELETE', '/comment/', true);
                xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
                xhr.onload = function(){};
                const data = 'poster=' + encodeURIComponent(current_poster) + '&post_number=' + encodeURIComponent(current_post_number) + '&comment_number=' + encodeURIComponent(current_comment_number);
                xhr.send(data);
            };
        })(poster, post_number, comment_number);
    } 
    
});
socket.on('delete_comment', function(data) {
    comment_id = data.poster + '_' + data.post_number + '_' + data.comment_number;
    console.log(comment_id);
    comment = document.getElementById(comment_id);
    if(comment){
        comment.remove();
    }
});