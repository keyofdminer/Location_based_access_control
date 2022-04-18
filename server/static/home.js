var colors = ["#00bc8c", "#3498DB", "#F39C12", "#6f42c1", "#375a7f", "#fd7e14"]

$(document).ready(function () {
    var view_w = 500;
    var view_h = 500;
    const scale_factor = 2.5;
    const svg = d3.select(".target").attr('viewBox', [0, 0, view_w, view_h]);

    var draw_circle = function (x, y, r, color) {
        svg
            .append('circle')
            .attr('cx', x)
            .attr('cy', y)
            .attr('r', r)
            .style('stroke', color)
            .style('opacity', 0.5)
            .style('fill', 'none');
    }
    
    var draw_point = function (x, y, color) {
        svg
            .append('circle')
            .attr('cx', x)
            .attr('cy', y)
            .attr('r', 3)
            .style('fill', color);
    }
    
    var draw_location = function (x, y) {
        svg
            .append('circle')
            .attr('cx', x)
            .attr('cy', y)
            .attr('r', 3)
            .style('fill', 'red');
    }
    
    var draw_rect = function (x, y) {
       
    }

    socket = io.connect("http://" + document.domain + ":" + location.port + "/");

    // Draw button click function
    $(`#setup`).on("click", function (e) {
        socket.emit("setup");
    });
    
    socket.emit("ready");
    
    socket.on("update_text", function (message) {
        document.getElementById('msg').innerHTML = message;
    });

    socket.on("draw_triangulation", function (message) {
        $(".target").empty();
        var xs = []
        var ys = []
        for (const [i, pi] of message["pis"].entries()) {
            xs.push(Math.abs(pi[0]))
            ys.push(Math.abs(pi[1]))
            if (i > colors.length -1){
                colors.push('#'+(Math.random() * 0xFFFFFF << 0).toString(16).padStart(6, '0'));
            }
        }

        var min_x = Math.min(...xs)
        var min_y = Math.min(...ys)
        var max_x = Math.max(...xs);
        var max_y = Math.max(...ys);

        var offset_x = (view_w - (max_x - min_x) * scale_factor) / 2;
        var offset_y = (view_h - (max_y - min_y) * scale_factor) / 2;

        for (var [i, pi] of message["pis"].entries()) {
            var x = (Math.abs(pi[0]) * scale_factor) + offset_x;
            var y = (Math.abs(pi[1]) * scale_factor) + offset_y;
            var r = (Math.abs(pi[2]) * scale_factor);

            color = colors[i]

            draw_point(x,y,color);
            draw_circle(x,y,r,color);
        }
        var location = message["location"]
        var x = (Math.abs(location[0]) * scale_factor) + offset_x;
        var y = (Math.abs(location[1]) * scale_factor) + offset_y;
        draw_location(x, y)
    });
});