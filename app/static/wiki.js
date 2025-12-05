(function () {
  const debounce = (fn, delay = 300) => {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), delay);
    };
  };

  const renderMarkdown = async (content) => {
    try {
      const response = await fetch('/render_markdown', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content }),
      });
      const data = await response.json();
      return data.html || '';
    } catch (e) {
      console.error('Preview error', e);
      return '<p class="text-red-600">Ошибка предпросмотра</p>';
    }
  };

  const initCodeCopy = () => {
    document.querySelectorAll('pre code').forEach((block) => {
      const wrapper = block.parentElement;
      if (wrapper.querySelector('.code-copy')) return;
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'code-copy';
      button.textContent = 'Copy';
      button.addEventListener('click', async () => {
        try {
          await navigator.clipboard.writeText(block.textContent);
          button.textContent = 'Copied';
          setTimeout(() => (button.textContent = 'Copy'), 1200);
        } catch (e) {
          button.textContent = 'Error';
          setTimeout(() => (button.textContent = 'Copy'), 1200);
        }
      });
      wrapper.appendChild(button);
    });
  };

  const initCopyButtons = () => {
    document.querySelectorAll('[data-copy-from]').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const target = document.getElementById(btn.dataset.copyFrom);
        if (!target) return;
        const text = target.textContent.trim();
        try {
          await navigator.clipboard.writeText(text);
          btn.textContent = 'Copied';
          setTimeout(() => (btn.textContent = 'Copy'), 1000);
        } catch (e) {
          btn.textContent = 'Error';
          setTimeout(() => (btn.textContent = 'Copy'), 1000);
        }
      });
    });
  };

  const initTreeNavigation = () => {
    const currentPath = document.body?.dataset?.currentPath || '';

    document.querySelectorAll('[data-tree-link]').forEach((link) => {
      if (currentPath && link.dataset.path === currentPath) {
        link.classList.add('is-active');
        let parent = link.closest('[data-tree-node]');
        while (parent) {
          const container = parent.querySelector('[data-tree-children]');
          if (container) container.classList.remove('hidden');
          const toggle = parent.querySelector('[data-tree-toggle]');
          if (toggle) toggle.setAttribute('aria-expanded', 'true');
          parent = parent.parentElement?.closest('[data-tree-node]');
        }
      }
    });

    document.querySelectorAll('[data-tree-toggle]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const target = btn.closest('[data-tree-node]')?.querySelector('[data-tree-children]');
        if (!target) return;
        const isHidden = target.classList.toggle('hidden');
        btn.setAttribute('aria-expanded', (!isHidden).toString());
        btn.querySelector('[data-icon]')?.classList.toggle('rotate-90', !isHidden);
      });
    });
  };

  const initToolbar = (toolbarId, textareaId) => {
    const toolbar = document.getElementById(toolbarId);
    const textarea = document.getElementById(textareaId);
    if (!toolbar || !textarea) return;

    const wrapSelection = (prefix, suffix = prefix) => {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const value = textarea.value;
      const selected = value.substring(start, end) || '';
      const before = value.substring(0, start);
      const after = value.substring(end);
      const insert = `${prefix}${selected || 'текст'}${suffix}`;
      textarea.value = `${before}${insert}${after}`;
      const caretStart = before.length + prefix.length;
      const caretEnd = caretStart + (selected || 'текст').length;
      textarea.focus();
      textarea.setSelectionRange(caretStart, caretEnd);
      textarea.dispatchEvent(new Event('input'));
    };

    const insertLine = (prefix, placeholder = 'элемент') => {
      const start = textarea.selectionStart;
      const value = textarea.value;
      const before = value.substring(0, start);
      const after = value.substring(start);
      const line = `${prefix}${placeholder}`;
      textarea.value = `${before}${line}\n${after}`;
      textarea.focus();
      const caret = before.length + prefix.length;
      textarea.setSelectionRange(caret, caret + placeholder.length);
      textarea.dispatchEvent(new Event('input'));
    };

    const actions = {
      bold: () => wrapSelection('**', '**'),
      italic: () => wrapSelection('*', '*'),
      code: () => wrapSelection('`', '`'),
      blockcode: () => wrapSelection('\n```\n', '\n```\n'),
      quote: () => insertLine('> ', 'цитата'),
      ul: () => insertLine('- ', 'элемент списка'),
      ol: () => insertLine('1. ', 'элемент списка'),
      link: () => wrapSelection('[', '](https://example.com)'),
      image: () => wrapSelection('![описание](', ')'),
      heading: (level) => insertLine('#'.repeat(level) + ' ', `Заголовок ${level}`),
    };

    toolbar.querySelectorAll('[data-action]').forEach((button) => {
      button.addEventListener('click', (e) => {
        e.preventDefault();
        const action = button.dataset.action;
        if (action === 'heading') {
          const level = Number(button.dataset.level || 2);
          actions.heading(level);
          return;
        }
        const fn = actions[action];
        if (fn) fn();
      });
    });
  };

  const initPreview = ({ textareaId, previewId, previewContainerId, triggerButtonId, autoCheckboxId, refreshButtonId, mode = 'auto' }) => {
    const textarea = document.getElementById(textareaId);
    const preview = document.getElementById(previewId);
    if (!textarea || !preview) return;
    const autoToggle = autoCheckboxId ? document.getElementById(autoCheckboxId) : null;
    const refreshBtn = refreshButtonId ? document.getElementById(refreshButtonId) : null;
    const triggerBtn = triggerButtonId ? document.getElementById(triggerButtonId) : null;
    const container = previewContainerId ? document.getElementById(previewContainerId) : null;

    const update = async () => {
      const html = await renderMarkdown(textarea.value);
      preview.innerHTML = html;
      if (window.hljs) {
        preview.querySelectorAll('pre code').forEach((block) => window.hljs.highlightElement(block));
      }
      initCodeCopy();
    };

    if (mode === 'manual') {
      const showPreview = () => {
        if (container) container.classList.remove('hidden');
        update();
      };
      if (triggerBtn) triggerBtn.addEventListener('click', (e) => { e.preventDefault(); showPreview(); });
    } else {
      const debounced = debounce(update, 350);
      const handler = () => {
        if (!autoToggle || autoToggle.checked) debounced();
      };
      textarea.addEventListener('input', handler);
      if (autoToggle) autoToggle.addEventListener('change', () => { if (autoToggle.checked) update(); });
      if (refreshBtn) refreshBtn.addEventListener('click', (e) => { e.preventDefault(); update(); });
      update();
    }
  };

  const initUnsavedGuard = () => {
    const guardedForms = document.querySelectorAll('form[data-guard-unsaved="true"]');
    if (!guardedForms.length) return;

    let dirty = false;
    const resetDirty = () => { dirty = false; };

    guardedForms.forEach((form) => {
      form.querySelectorAll('textarea, input, select').forEach((el) => {
        el.addEventListener('input', () => { dirty = true; });
        el.addEventListener('change', () => { dirty = true; });
      });
      form.addEventListener('submit', resetDirty);
    });

    window.addEventListener('beforeunload', (e) => {
      if (!dirty) return;
      e.preventDefault();
      e.returnValue = '';
    });
  };

  const initUploadDrop = () => {
    const drop = document.getElementById('upload-drop');
    const fileInput = document.getElementById('file');
    if (!drop || !fileInput) return;

    ['dragenter', 'dragover'].forEach((evt) => {
      drop.addEventListener(evt, (e) => {
        e.preventDefault();
        drop.classList.add('ring-2', 'ring-blue-500');
      });
    });

    ['dragleave', 'drop'].forEach((evt) => {
      drop.addEventListener(evt, (e) => {
        e.preventDefault();
        drop.classList.remove('ring-2', 'ring-blue-500');
      });
    });

    drop.addEventListener('drop', (e) => {
      if (!e.dataTransfer?.files?.length) return;
      fileInput.files = e.dataTransfer.files;
    });

    drop.addEventListener('click', () => fileInput.click());
  };

  const initPathBuilder = ({ folderSelectId, nameInputId, pathInputId }) => {
    const folder = document.getElementById(folderSelectId);
    const name = document.getElementById(nameInputId);
    const hidden = document.getElementById(pathInputId);
    if (!folder || !name || !hidden) return;

    const rebuild = () => {
      const folderValue = folder.value.trim();
      const nameValue = name.value.trim();
      const parts = [];
      if (folderValue) parts.push(folderValue.replace(/^\/+|\/+$/g, ''));
      if (nameValue) parts.push(nameValue.replace(/^\/+|\/+$/g, ''));
      hidden.value = parts.filter(Boolean).join('/');
    };

    folder.addEventListener('change', rebuild);
    name.addEventListener('input', rebuild);
    rebuild();
  };

  const initImageUploaders = () => {
    document.querySelectorAll('[data-upload-target]').forEach((block) => {
      const textareaId = block.dataset.uploadTarget;
      const textarea = document.getElementById(textareaId);
      const input = block.querySelector('input[type="file"]');
      const button = block.querySelector('[data-upload-btn]');
      if (!textarea || !input || !button) return;

      button.addEventListener('click', async (e) => {
        e.preventDefault();
        if (!input.files || !input.files.length) {
          button.textContent = 'Выберите файл';
          setTimeout(() => (button.textContent = 'Загрузить и вставить'), 1200);
          return;
        }

        const formData = new FormData();
        formData.append('file', input.files[0]);
        button.disabled = true;
        const original = button.textContent;
        button.textContent = 'Загрузка...';

        try {
          const resp = await fetch('/upload', {
            method: 'POST',
            headers: { Accept: 'application/json' },
            body: formData,
          });
          if (!resp.ok) throw new Error('upload failed');
          const data = await resp.json();
          const url = data.url || (data.filename ? `/uploads/${data.filename}` : '');
          if (url) {
            const snippet = `![описание](${url})`;
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            const value = textarea.value;
            textarea.value = `${value.slice(0, start)}${snippet}${value.slice(end)}`;
            textarea.focus();
            const caret = start + snippet.length;
            textarea.setSelectionRange(caret, caret);
            textarea.dispatchEvent(new Event('input'));
            button.textContent = 'Вставлено';
          } else {
            button.textContent = 'Ошибка';
          }
        } catch (err) {
          button.textContent = 'Ошибка';
        } finally {
          setTimeout(() => {
            button.textContent = original;
            button.disabled = false;
          }, 1200);
        }
      });
    });
  };

  window.WikiUI = {
    initTreeNavigation,
    initCodeCopy,
    initCopyButtons,
    initToolbar,
    initPreview,
    initUnsavedGuard,
    initUploadDrop,
    initPathBuilder,
    initImageUploaders,
  };
})();
