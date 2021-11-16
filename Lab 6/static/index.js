const socket = io();
socket.on('connect', () => {
//   socket.onAny((event, ...args) => {
//   console.log(Date.now(),event, args);
// });
});

socket.on('disconnect', () => {
  console.log('disconnect')
});

setInterval(() => {
  socket.emit('ping-gps', 'dat')
}, 100)


var vlSpec = {
  $schema: 'https://vega.github.io/schema/vega-lite/v5.json',
  data: {name: 'table'},
  width: 400,
  mark: 'line',
  encoding: {
    x: {field: 'x', type: 'quantitative', scale: {zero: false}},
    y: {field: 'y', type: 'quantitative'},
    color: {field: 'category', type: 'nominal'}
  }
};

vegaEmbed('#chart', vlSpec).then( (res) => {
  let  x, y, z;
  let counter = -1;
  let cat = ['x', 'y', 'z']
  let minimumX = -100;
   socket.on('pong-gps', (new_x,new_y,new_z) => {
    counter++;
    minimumX++;
    const newVals = [new_x, new_y, new_z].map((c,v) => {
      return {
      x: counter,
      y: c,
      category: cat[v]
    };
  })
    const changeSet = vega
      .changeset()
      .insert(newVals)
      .remove( (t) => {
        return t.x < minimumX;
      });
    res.view.change('table', changeSet).run();
  })

})
