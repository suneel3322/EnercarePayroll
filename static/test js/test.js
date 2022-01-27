var trace1 = {
    x: [
        {% for name in agent_name %}
        '{{name}}',
        {% endfor %}
    ],
    y: [10, 15, 13, 17],
    type: 'scatter'
  };
  
  var trace2 = {
    x: [
        {% for name in agent_name %}
        '{{name}}',
        {% endfor %}
    ],
    y: [16, 5, 11, 9],
    type: 'scatter'
  };
  
  var data = [trace1, trace2];
  
  Plotly.newPlot('mychart', data);