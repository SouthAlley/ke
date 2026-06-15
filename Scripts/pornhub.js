// 2026-06-15 12:45

let body = $response.body;

// 1. 移除特定的广告容器 (CSS 样式覆盖)
// 匹配文件中的 .globalCookieBanner, .ad-placeholder 等类名并强制隐藏
const adSelectors = [
    ".globalCookieBanner", "#cookieBanner", ".cookieBannerV1", 
    "div[class*='ad-']", "div[id*='ad-']", ".adContainer", 
    ".adWrapper", ".mg_ad_native", ".bottomNotification", 
    ".premiumPromoBanner", ".ad-placeholder", ".ad-box", 
    ".ad_wrapper", ".ads-container", ".video-wrapper-ad", ".ad-item"
];

const cssInjection = `
<style>
    ${adSelectors.join(", ")} {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
        min-height: 0 !important;
        border: none !important;
    }
</style>`;

// 2. 注入 JS 逻辑拦截跳转
// 劫持 location 对象及重写导航 API
const jsInjection = `
<script>
    (function() {
        const blockUrl = (url) => typeof url === 'string' && url.includes('interstitial');
        
        // 劫持 location.href
        const proto = Object.getPrototypeOf(window.location);
        const originalHref = Object.getOwnPropertyDescriptor(proto, 'href');
        Object.defineProperty(window.location, 'href', {
            set: function(val) { if (!blockUrl(val)) originalHref.set.call(this, val); }
        });

        // 拦截 assign 和 replace
        window.location.assign = new Proxy(window.location.assign, {
            apply: (t, self, args) => { if (!blockUrl(args[0])) return t.apply(self, args); }
        });
        window.location.replace = new Proxy(window.location.replace, {
            apply: (t, self, args) => { if (!blockUrl(args[0])) return t.apply(self, args); }
        });

        // 阻止点击事件触发的跳转
        document.addEventListener('click', (e) => {
            let target = e.target.closest('a');
            if (target && target.href && blockUrl(target.href)) {
                e.preventDefault();
                e.stopPropagation();
            }
        }, true);
    })();
</script>`;

// 插入到 <head> 之后
body = body.replace(/(<head[^>]*>)/i, '$1' + cssInjection + jsInjection);

$done({ body });
