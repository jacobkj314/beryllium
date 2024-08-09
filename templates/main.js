var socket = io();

//this allows the server to send posts to the client
socket.on('add_post', function(data) {
    poster = data.poster;
    post_number = data.post_number;
    new_post = data.new_post;

    console.log('new post by ' + poster + ', current user is {{ current_user.username }}')

    
    post_id = "post_" + poster + "_" + post_number
    if(! document.getElementById(post_id)){ //check whether this post already exists
        //insert post
        post_container = document.getElementById(poster == '{{ current_user.username }}' ? "current_user_content" : "other_user_content");
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
    }
});

//this allows the server to send individual comments
socket.on('add_comment', function(data) {
    console.log(data.poster + ' ' + data.post_number)
    console.log(data.new_comment)
    comment_section_id = 'user_' + data.poster + '_post_' + data.post_number + '_comments';
    document.getElementById(comment_section_id).insertAdjacentHTML('beforeend', data.new_comment);
});