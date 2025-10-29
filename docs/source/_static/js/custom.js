/**
 * ===============================================================================
 * Frame Python Documentation - Enhanced JavaScript
 * ===============================================================================
 * Provides sophisticated interactions, accessibility, and UX enhancements
 * for the Frame Python documentation site using the Shibuya theme.
 * ===============================================================================
 */

// Frame Documentation namespace
const FrameDocs = {
    // Configuration
    config: {
        animationDuration: 300,
        scrollOffset: 80,
        debounceDelay: 150,
        searchMinLength: 2
    },

    // Utilities
    utils: {
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        throttle(func, limit) {
            let inThrottle;
            return function() {
                const args = arguments;
                const context = this;
                if (!inThrottle) {
                    func.apply(context, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        },

        addClass(element, className) {
            if (element && !element.classList.contains(className)) {
                element.classList.add(className);
            }
        },

        removeClass(element, className) {
            if (element && element.classList.contains(className)) {
                element.classList.remove(className);
            }
        },

        // Smooth scroll with custom easing
        smoothScrollTo(target, offset = 0, duration = 800) {
            const targetElement = typeof target === 'string' ? document.querySelector(target) : target;
            if (!targetElement) return;

            const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - offset;
            const startPosition = window.pageYOffset;
            const distance = targetPosition - startPosition;
            let startTime = null;

            function ease(t, b, c, d) {
                t /= d / 2;
                if (t < 1) return c / 2 * t * t + b;
                t--;
                return -c / 2 * (t * (t - 2) - 1) + b;
            }

            function animation(currentTime) {
                if (startTime === null) startTime = currentTime;
                const timeElapsed = currentTime - startTime;
                const run = ease(timeElapsed, startPosition, distance, duration);
                window.scrollTo(0, run);
                if (timeElapsed < duration) requestAnimationFrame(animation);
            }

            requestAnimationFrame(animation);
        },

        // Create notification toast
        showNotification(message, type = 'info', duration = 3000) {
            const notification = document.createElement('div');
            notification.className = `frame-notification frame-notification--${type}`;
            notification.innerHTML = `
                <div class="frame-notification__content">
                    <span class="frame-notification__message">${message}</span>
                    <button class="frame-notification__close" aria-label="Close notification">×</button>
                </div>
            `;

            document.body.appendChild(notification);

            // Close button functionality
            notification.querySelector('.frame-notification__close').addEventListener('click', () => {
                this.hideNotification(notification);
            });

            // Auto-hide after duration
            setTimeout(() => {
                this.hideNotification(notification);
            }, duration);

            // Animate in
            requestAnimationFrame(() => {
                notification.classList.add('frame-notification--visible');
            });

            return notification;
        },

        hideNotification(notification) {
            notification.classList.remove('frame-notification--visible');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, this.config.animationDuration);
        }
    },

    // =================== SIDEBAR MANAGEMENT (SHIBUYA ENHANCEMENT) ===================
    sidebar: {
        init() {
            console.log('Initializing Shibuya sidebar enhancements...');
            this.enhanceShibuyaCollapse();
            this.improveKeyboardNav();
        },

        enhanceShibuyaCollapse() {
            // Shibuya already handles collapse/expand, we just add visual enhancements
            const globaltoc = document.querySelector('.globaltoc');
            if (!globaltoc) {
                console.log('No globaltoc found');
                return;
            }

            // Add smooth transitions and animations
            const collapseButtons = globaltoc.querySelectorAll('._collapse > button');
            console.log(`Enhanced ${collapseButtons.length} Shibuya collapse buttons`);
            
            // Add tooltip to buttons for better UX
            collapseButtons.forEach(button => {
                button.addEventListener('mouseenter', () => {
                    const isCollapsed = button.parentElement.classList.contains('_collapse');
                    button.title = isCollapsed ? 'Expand section' : 'Collapse section';
                });
            });
        },

        improveKeyboardNav() {
            // Enhance keyboard navigation for sidebar
            const globaltoc = document.querySelector('.globaltoc');
            if (!globaltoc) return;

            // Add keyboard shortcuts for quick navigation
            document.addEventListener('keydown', (e) => {
                // Alt + [ to collapse all
                if (e.altKey && e.key === '[') {
                    e.preventDefault();
                    this.collapseAll();
                }
                // Alt + ] to expand all
                if (e.altKey && e.key === ']') {
                    e.preventDefault();
                    this.expandAll();
                }
            });
        },

        collapseAll() {
            const globaltoc = document.querySelector('.globaltoc');
            if (!globaltoc) return;

            const expanded = globaltoc.querySelectorAll('li:not(._collapse)');
            expanded.forEach(item => {
                const button = item.querySelector('button');
                if (button) button.click();
            });
            console.log('Collapsed all sections');
        },

        expandAll() {
            const globaltoc = document.querySelector('.globaltoc');
            if (!globaltoc) return;

            const collapsed = globaltoc.querySelectorAll('._collapse > button');
            collapsed.forEach(button => button.click());
            console.log('Expanded all sections');
        }
    },

    // Enhanced code block functionality
    codeBlocks: {
        init() {
            this.enhanceCodeBlocks();
            this.addLineNumbers();
            this.addCopyFunctionality();
            this.addLanguageLabels();
        },

        enhanceCodeBlocks() {
            const codeBlocks = document.querySelectorAll('.highlight');
            codeBlocks.forEach((block, index) => {
                block.classList.add('frame-code-block');
                block.setAttribute('data-code-block-id', index);
                
                // Add wrapper for better styling control
                if (!block.querySelector('.frame-code-wrapper')) {
                    const pre = block.querySelector('pre');
                    if (pre) {
                        const wrapper = document.createElement('div');
                        wrapper.className = 'frame-code-wrapper';
                        pre.parentNode.insertBefore(wrapper, pre);
                        wrapper.appendChild(pre);
                    }
                }
            });
        },

        addLineNumbers() {
            const codeBlocks = document.querySelectorAll('.highlight pre');
            codeBlocks.forEach(pre => {
                const code = pre.querySelector('code');
                if (code && !pre.querySelector('.line-numbers')) {
                    const lines = code.textContent.split('\n').length;
                    if (lines > 3) { // Only add line numbers for longer code blocks
                        const lineNumbersDiv = document.createElement('div');
                        lineNumbersDiv.className = 'line-numbers';
                        lineNumbersDiv.setAttribute('aria-hidden', 'true');
                        
                        for (let i = 1; i <= lines; i++) {
                            const lineNumber = document.createElement('span');
                            lineNumber.textContent = i;
                            lineNumbersDiv.appendChild(lineNumber);
                        }
                        
                        pre.insertBefore(lineNumbersDiv, code);
                        pre.classList.add('has-line-numbers');
                    }
                }
            });
        },

        addCopyFunctionality() {
            const codeBlocks = document.querySelectorAll('.highlight');
            codeBlocks.forEach(block => {
                if (!block.querySelector('.frame-copy-button')) {
                    const copyButton = document.createElement('button');
                    copyButton.className = 'frame-copy-button';
                    copyButton.innerHTML = `
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                        </svg>
                        <span>Copy</span>
                    `;
                    copyButton.setAttribute('aria-label', 'Copy code to clipboard');
                    
                    copyButton.addEventListener('click', () => {
                        this.copyCodeToClipboard(block, copyButton);
                    });
                    
                    block.appendChild(copyButton);
                }
            });
        },

        addLanguageLabels() {
            const codeBlocks = document.querySelectorAll('.highlight');
            codeBlocks.forEach(block => {
                const className = block.className;
                const languageMatch = className.match(/highlight-(\w+)/);
                if (languageMatch && !block.querySelector('.frame-language-label')) {
                    const language = languageMatch[1];
                    const label = document.createElement('span');
                    label.className = 'frame-language-label';
                    label.textContent = language.toUpperCase();
                    block.appendChild(label);
                }
            });
        },

        async copyCodeToClipboard(codeBlock, button) {
            const code = codeBlock.querySelector('code');
            if (!code) return;

            const text = code.textContent || code.innerText;
            
            try {
                await navigator.clipboard.writeText(text);
                this.showCopySuccess(button);
                FrameDocs.utils.showNotification('Code copied to clipboard!', 'success', 2000);
            } catch (err) {
                // Fallback for older browsers
                this.fallbackCopy(text);
                this.showCopySuccess(button);
            }
        },

        showCopySuccess(button) {
            const originalContent = button.innerHTML;
            button.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20,6 9,17 4,12"></polyline>
                </svg>
                <span>Copied!</span>
            `;
            button.classList.add('copied');
            
            setTimeout(() => {
                button.innerHTML = originalContent;
                button.classList.remove('copied');
            }, 2000);
        },

        fallbackCopy(text) {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'absolute';
            textArea.style.left = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {
                document.execCommand('copy');
            } catch (err) {
                console.error('Fallback copy failed', err);
            }
            
            document.body.removeChild(textArea);
        }
    },

    // Enhanced navigation
    navigation: {
        init() {
            this.enhanceTableOfContents();
            this.addScrollSpy();
            this.enhanceMobileNavigation();
            this.addKeyboardNavigation();
        },

        enhanceTableOfContents() {
            const toc = document.querySelector('.toctree-wrapper');
            if (toc) {
                toc.classList.add('frame-enhanced-toc');
                
                // Add expand/collapse functionality for nested items
                const tocItems = toc.querySelectorAll('.toctree-l1');
                tocItems.forEach(item => {
                    const sublist = item.querySelector('ul');
                    if (sublist) {
                        const link = item.querySelector('a');
                        if (link) {
                            const toggle = document.createElement('button');
                            toggle.className = 'toc-toggle';
                            toggle.innerHTML = '▶';
                            toggle.setAttribute('aria-label', 'Toggle subsection');
                            
                            toggle.addEventListener('click', (e) => {
                                e.preventDefault();
                                item.classList.toggle('expanded');
                                toggle.innerHTML = item.classList.contains('expanded') ? '▼' : '▶';
                            });
                            
                            link.parentNode.insertBefore(toggle, link);
                        }
                    }
                });
            }
        },

        addScrollSpy() {
            const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
            const tocLinks = document.querySelectorAll('.toctree-wrapper a');
            
            if (headings.length === 0 || tocLinks.length === 0) return;

            const observerOptions = {
                rootMargin: '-20% 0px -70% 0px',
                threshold: 0
            };

            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const id = entry.target.id;
                        if (id) {
                            // Remove active class from all TOC links
                            tocLinks.forEach(link => link.classList.remove('active'));
                            
                            // Add active class to current section
                            const activeLink = document.querySelector(`.toctree-wrapper a[href="#${id}"]`);
                            if (activeLink) {
                                activeLink.classList.add('active');
                            }
                        }
                    }
                });
            }, observerOptions);

            headings.forEach(heading => {
                if (heading.id) {
                    observer.observe(heading);
                }
            });
        },

        enhanceMobileNavigation() {
            // Add mobile menu toggle if needed
            const mobileBreakpoint = 768;
            
            const handleResize = FrameDocs.utils.throttle(() => {
                const isMobile = window.innerWidth <= mobileBreakpoint;
                document.body.classList.toggle('mobile-view', isMobile);
            }, 100);

            window.addEventListener('resize', handleResize);
            handleResize(); // Initial check
        },

        addKeyboardNavigation() {
            document.addEventListener('keydown', (e) => {
                // Quick navigation shortcuts
                if (e.altKey) {
                    switch (e.key) {
                        case '1':
                            e.preventDefault();
                            this.navigateToSection('h1');
                            break;
                        case '2':
                            e.preventDefault();
                            this.navigateToSection('h2');
                            break;
                        case 'h':
                            e.preventDefault();
                            window.location.href = '#';
                            break;
                    }
                }
            });
        },

        navigateToSection(selector) {
            const heading = document.querySelector(selector);
            if (heading) {
                FrameDocs.utils.smoothScrollTo(heading, FrameDocs.config.scrollOffset);
            }
        }
    },

    // Enhanced search functionality
    search: {
        init() {
            this.enhanceSearchField();
            this.addSearchShortcuts();
        },

        enhanceSearchField() {
            const searchField = document.querySelector('.search-field input, input[type="search"]');
            if (searchField) {
                searchField.addEventListener('input', FrameDocs.utils.debounce((e) => {
                    this.handleSearchInput(e.target.value);
                }, FrameDocs.config.debounceDelay));

                // Add search suggestions placeholder
                const searchContainer = searchField.parentNode;
                if (searchContainer && !searchContainer.querySelector('.search-suggestions')) {
                    const suggestions = document.createElement('div');
                    suggestions.className = 'search-suggestions';
                    searchContainer.appendChild(suggestions);
                }
            }
        },

        addSearchShortcuts() {
            document.addEventListener('keydown', (e) => {
                // Ctrl/Cmd + K for search focus
                if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                    e.preventDefault();
                    const searchField = document.querySelector('.search-field input, input[type="search"]');
                    if (searchField) {
                        searchField.focus();
                        searchField.select();
                    }
                }

                // Escape to clear search
                if (e.key === 'Escape') {
                    const searchField = document.querySelector('.search-field input, input[type="search"]');
                    if (searchField && document.activeElement === searchField) {
                        searchField.blur();
                        searchField.value = '';
                        this.clearSearchSuggestions();
                    }
                }
            });
        },

        handleSearchInput(query) {
            if (query.length >= FrameDocs.config.searchMinLength) {
                // Implement client-side search or API call here
                console.log('Searching for:', query);
            } else {
                this.clearSearchSuggestions();
            }
        },

        clearSearchSuggestions() {
            const suggestions = document.querySelector('.search-suggestions');
            if (suggestions) {
                suggestions.innerHTML = '';
                suggestions.classList.remove('active');
            }
        }
    },

    // Theme and accessibility
    accessibility: {
        init() {
            this.enhanceKeyboardNavigation();
            this.addSkipLinks();
            this.improveScreenReaderSupport();
            this.addFocusIndicators();
        },

        enhanceKeyboardNavigation() {
            // Make all interactive elements keyboard accessible
            const interactiveElements = document.querySelectorAll('a, button, input, select, textarea, [tabindex]');
            
            interactiveElements.forEach(element => {
                if (!element.getAttribute('tabindex') && element.tagName !== 'INPUT' && element.tagName !== 'TEXTAREA' && element.tagName !== 'SELECT') {
                    element.setAttribute('tabindex', '0');
                }
            });
        },

        addSkipLinks() {
            if (!document.querySelector('.skip-links')) {
                const skipLinks = document.createElement('nav');
                skipLinks.className = 'skip-links';
                skipLinks.innerHTML = `
                    <a href="#main-content" class="skip-link">Skip to main content</a>
                    <a href="#navigation" class="skip-link">Skip to navigation</a>
                `;
                document.body.insertBefore(skipLinks, document.body.firstChild);
            }
        },

        improveScreenReaderSupport() {
            // Add ARIA labels where missing
            const codeBlocks = document.querySelectorAll('pre code');
            codeBlocks.forEach((code, index) => {
                if (!code.getAttribute('aria-label')) {
                    const language = this.getCodeLanguage(code);
                    code.setAttribute('aria-label', `Code block ${index + 1}${language ? ` in ${language}` : ''}`);
                }
            });

            // Improve table accessibility
            const tables = document.querySelectorAll('table');
            tables.forEach(table => {
                if (!table.getAttribute('role')) {
                    table.setAttribute('role', 'table');
                }
                
                // Add caption if missing
                if (!table.querySelector('caption') && table.querySelector('thead th')) {
                    const firstHeader = table.querySelector('thead th');
                    if (firstHeader) {
                        const caption = document.createElement('caption');
                        caption.textContent = `Table with information about ${firstHeader.textContent}`;
                        caption.className = 'sr-only';
                        table.insertBefore(caption, table.firstChild);
                    }
                }
            });
        },

        getCodeLanguage(codeElement) {
            const pre = codeElement.closest('pre');
            if (pre) {
                const classList = pre.parentNode.classList;
                for (let className of classList) {
                    if (className.startsWith('highlight-')) {
                        return className.replace('highlight-', '');
                    }
                }
            }
            return null;
        },

        addFocusIndicators() {
            // Enhanced focus indicators for better accessibility
            const style = document.createElement('style');
            style.textContent = `
                .frame-focus-indicator {
                    outline: 2px solid var(--frame-primary);
                    outline-offset: 2px;
                    border-radius: 4px;
                }
            `;
            document.head.appendChild(style);

            // Add focus indicators to interactive elements
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    document.body.classList.add('keyboard-navigation');
                }
            });

            document.addEventListener('mousedown', () => {
                document.body.classList.remove('keyboard-navigation');
            });
        }
    },

    // Tree View Enhancement
    treeView: {
        init() {
            console.log('Initializing tree view enhancements...');
            this.makeCollapsible();
            this.setupKeyboardNav();
        },

        makeCollapsible() {
            const treeview = document.querySelector('.treeview.docutils.container');
            if (!treeview) {
                console.log('No treeview found');
                return;
            }

            // Find all nested lists and make them collapsible
            const processNestedLists = (ul, depth = 1) => {
                if (!ul) return;
                
                const items = ul.querySelectorAll(':scope > li');
                items.forEach(li => {
                    const nestedUl = li.querySelector(':scope > ul');
                    if (nestedUl) {
                        // Add toggle button for all folders with nested content
                        const firstP = li.querySelector(':scope > p');
                        if (firstP && !firstP.querySelector('.tree-toggle')) {
                            const toggle = document.createElement('button');
                            toggle.className = 'tree-toggle';
                            toggle.innerHTML = '<span class="tree-toggle-icon">▼</span>';
                            toggle.setAttribute('type', 'button');
                            
                            // All folders are expanded by default (down to file level)
                            const shouldCollapse = false;
                            
                            toggle.setAttribute('aria-expanded', 'true');
                            toggle.setAttribute('aria-label', 'Toggle folder');
                            toggle.title = 'Click to collapse/expand';
                            
                            if (shouldCollapse) {
                                nestedUl.classList.add('collapsed');
                                li.classList.add('collapsed');
                                toggle.querySelector('.tree-toggle-icon').innerHTML = '▶';
                                toggle.setAttribute('aria-expanded', 'false');
                            }
                            
                            toggle.addEventListener('click', (e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                this.toggleNode(li, nestedUl, toggle);
                            });
                            
                            firstP.insertBefore(toggle, firstP.firstChild);
                        }
                        
                        // Process nested items recursively (all depths)
                        processNestedLists(nestedUl, depth + 1);
                    }
                });
            };
            
            const rootUl = treeview.querySelector('ul');
            processNestedLists(rootUl, 1);
            
            console.log('Tree view made collapsible with all folders expanded by default');
        },

        toggleNode(li, ul, toggle) {
            const isCollapsed = ul.classList.contains('collapsed');
            
            if (isCollapsed) {
                // Expand
                ul.classList.remove('collapsed');
                li.classList.remove('collapsed');
                toggle.setAttribute('aria-expanded', 'true');
                toggle.querySelector('.tree-toggle-icon').innerHTML = '▼';
            } else {
                // Collapse
                ul.classList.add('collapsed');
                li.classList.add('collapsed');
                toggle.setAttribute('aria-expanded', 'false');
                toggle.querySelector('.tree-toggle-icon').innerHTML = '▶';
            }
        },

        setupKeyboardNav() {
            document.addEventListener('keydown', (e) => {
                const treeview = document.querySelector('.treeview.docutils.container');
                if (!treeview) return;

                // Alt + E to expand all tree nodes
                if (e.altKey && e.key === 'e') {
                    e.preventDefault();
                    this.expandAll();
                }
                
                // Alt + C to collapse all tree nodes
                if (e.altKey && e.key === 'c') {
                    e.preventDefault();
                    this.collapseAll();
                }
            });
        },

        expandAll() {
            const toggles = document.querySelectorAll('.treeview .tree-toggle');
            toggles.forEach(toggle => {
                const li = toggle.closest('li');
                const ul = li.querySelector(':scope > ul');
                if (ul && ul.classList.contains('collapsed')) {
                    this.toggleNode(li, ul, toggle);
                }
            });
            FrameDocs.utils.showNotification('All tree nodes expanded', 'info', 2000);
        },

        collapseAll() {
            const toggles = document.querySelectorAll('.treeview .tree-toggle');
            toggles.forEach(toggle => {
                const li = toggle.closest('li');
                const ul = li.querySelector(':scope > ul');
                if (ul && !ul.classList.contains('collapsed')) {
                    this.toggleNode(li, ul, toggle);
                }
            });
            FrameDocs.utils.showNotification('All tree nodes collapsed', 'info', 2000);
        }
    },

    // Performance monitoring
    performance: {
        init() {
            this.measurePageLoad();
            this.optimizeImages();
            this.lazyLoadContent();
        },

        measurePageLoad() {
            window.addEventListener('load', () => {
                if ('performance' in window) {
                    const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
                    console.log(`Frame Docs loaded in ${loadTime}ms`);
                    
                    // Send to analytics if configured
                    if (window.gtag) {
                        gtag('event', 'page_load_time', {
                            value: loadTime,
                            custom_parameter: 'frame_docs'
                        });
                    }
                }
            });
        },

        optimizeImages() {
            const images = document.querySelectorAll('img');
            images.forEach(img => {
                if (!img.getAttribute('loading')) {
                    img.setAttribute('loading', 'lazy');
                }
                
                img.addEventListener('load', function() {
                    this.classList.add('loaded');
                }, { once: true });

                img.addEventListener('error', function() {
                    this.classList.add('error');
                    console.warn('Failed to load image:', this.src);
                }, { once: true });
            });
        },

        lazyLoadContent() {
            if ('IntersectionObserver' in window) {
                const lazyElements = document.querySelectorAll('[data-lazy]');
                
                const lazyObserver = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const element = entry.target;
                            element.classList.add('loaded');
                            lazyObserver.unobserve(element);
                        }
                    });
                });

                lazyElements.forEach(element => {
                    lazyObserver.observe(element);
                });
            }
        }
    },

    // Initialize all modules
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.initializeModules();
            });
        } else {
            this.initializeModules();
        }
    },

    initializeModules() {
        console.log('🚀 Initializing Frame Python Documentation enhancements...');
        
        try {
            this.sidebar.init();
            console.log('✅ Sidebar collapsed and enhanced');
            
            this.codeBlocks.init();
            console.log('✅ Code blocks enhanced');
            
            this.navigation.init();
            console.log('✅ Navigation enhanced');
            
            this.search.init();
            console.log('✅ Search enhanced');
            
            this.accessibility.init();
            console.log('✅ Accessibility enhanced');
            
            this.treeView.init();
            console.log('✅ Tree view enhanced with collapsible nodes');
            
            this.performance.init();
            console.log('✅ Performance monitoring initialized');
            
            // Add custom notification styles
            this.addNotificationStyles();
            
            // Initialize theme detection
            this.initializeThemeDetection();
            
            console.log('🎉 Frame Python Documentation fully loaded and enhanced!');
            
        } catch (error) {
            console.error('❌ Error initializing Frame Docs:', error);
        }
    },

    addNotificationStyles() {
        if (!document.querySelector('#frame-notification-styles')) {
            const style = document.createElement('style');
            style.id = 'frame-notification-styles';
            style.textContent = `
                .frame-notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: var(--frame-surface-elevated);
                    border: 1px solid var(--frame-border);
                    border-radius: 12px;
                    padding: 16px;
                    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
                    z-index: 10000;
                    transform: translateX(400px);
                    opacity: 0;
                    transition: all 0.3s ease;
                    max-width: 400px;
                }
                
                .frame-notification--visible {
                    transform: translateX(0);
                    opacity: 1;
                }
                
                .frame-notification--success {
                    border-left: 4px solid var(--frame-green-success);
                }
                
                .frame-notification--warning {
                    border-left: 4px solid var(--frame-yellow-warning);
                }
                
                .frame-notification--error {
                    border-left: 4px solid var(--frame-red-error);
                }
                
                .frame-notification__content {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 12px;
                }
                
                .frame-notification__close {
                    background: none;
                    border: none;
                    font-size: 20px;
                    cursor: pointer;
                    color: var(--frame-text-secondary);
                    padding: 0;
                    width: 24px;
                    height: 24px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 4px;
                }
                
                .frame-notification__close:hover {
                    background: var(--frame-border-light);
                    color: var(--frame-text-primary);
                }
                
                .skip-links {
                    position: absolute;
                    top: -200px;
                    left: 0;
                    z-index: 10001;
                }
                
                .skip-link {
                    position: absolute;
                    background: var(--frame-primary);
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    text-decoration: none;
                    font-weight: 500;
                }
                
                .skip-link:focus {
                    top: 10px;
                    left: 10px;
                }
            `;
            document.head.appendChild(style);
        }
    },

    initializeThemeDetection() {
        // Detect and respond to theme changes
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
        
        function handleThemeChange(e) {
            document.body.classList.toggle('prefers-dark', e.matches);
            console.log(`Theme preference: ${e.matches ? 'dark' : 'light'}`);
        }
        
        prefersDark.addEventListener('change', handleThemeChange);
        handleThemeChange(prefersDark); // Initial check
    }
};

// Initialize the documentation enhancements
FrameDocs.init();
