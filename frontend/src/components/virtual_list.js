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
        // Validate input: accept arrays, iterables, or null/undefined; otherwise throw
        if (Array.isArray(items)) {
            this.items = items;
        } else if (items == null) {
            this.items = [];
        } else if (typeof items[Symbol.iterator] === 'function') {
            // Accept any iterable by coercing to an array
            this.items = Array.from(items);
        } else {
            throw new TypeError('VirtualList.setItems expects an array or iterable');
        }
        this.render();
    }

    render() {
        // Construct nodes directly to avoid injecting untrusted HTML (XSS-safe)
        // Clear existing children
        while (this.root.firstChild) {
            this.root.removeChild(this.root.firstChild);
        }
        for (const i of this.items) {
            const node = document.createElement('div');
            node.className = 'virtual-item';
            node.textContent = String(i && i.name != null ? i.name : '');
            this.root.appendChild(node);
        }
    }
}
