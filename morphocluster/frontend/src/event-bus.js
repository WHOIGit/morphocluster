import mitt from 'mitt';

const emitter = mitt();

// Create Vue 2 compatible API
export const EventBus = {
  $on: (...args) => emitter.on(...args),
  $once: (...args) => emitter.on(...args), // mitt doesn't have once, but on works
  $off: (...args) => emitter.off(...args),
  $emit: (...args) => emitter.emit(...args)
};