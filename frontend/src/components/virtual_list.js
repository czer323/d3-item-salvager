// Minimal virtual list stub (T013)
// This file intentionally keeps behavior small and testable; it will be
// expanded with virtualization logic as needed.

export class VirtualList {
  constructor(rootEl, options = {}) {
    this.root = rootEl;
    this.options = options;
    this.items = [];
  }

  setItems(items) {
    this.items = items;
    this.render();
  }

  render() {
    this.root.innerHTML = this.items.map(i => `<div class="virtual-item">${i.name}</div>`).join('');
  }
}
