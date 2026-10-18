/*
 * 咕咚(Codoon)校园跑 —— 高德定位 SDK 注入脚本
 *
 * 原理：咕咚内部用的是高德定位 SDK（com.amap.api.location.AMapLocation）。
 *      本脚本在咕咚进程里改写 AMapLocation 的经纬度/速度/精度等 getter，
 *      让咕咚以为你正沿着下面这条闭环路线以固定速度跑步。
 *
 * 需要改的地方只有两处：
 *   1) V 数组：路线顶点 [纬度, 经度]，首尾自动闭合
 *      ★ 换路线看 使用指南.md 第 7 节：必须用高德系工具取点（GCJ-02），
 *        百度(BD09)/Google(WGS84) 的坐标会整体偏 300-600 米。
 *   2) SPEED：速度，单位 m/s（3.0 m/s ≈ 10.8 km/h）
 */
Java.perform(function () {
    // ==== 路线顶点（示例：一条 13 点闭环，约 362 米；换成你学校那一圈）====
    var V = [
        [22.683782507837485, 114.20262284760585],
        [22.683603975223065, 114.20236880188534],
        [22.682771531234145, 114.20244950895719],
        [22.68265419983294, 114.20257452731329],
        [22.682595124009588, 114.20277347569322],
        [22.682610401991504, 114.20305575851768],
        [22.68276762232778, 114.20312699083534],
        [22.682919844010154, 114.20316462043903],
        [22.68311651588592, 114.20314713184051],
        [22.683303257316858, 114.20310679439785],
        [22.68368417628767, 114.20303687159422],
        [22.68377416617212, 114.20282985751389],
        [22.68377880043065, 114.20262553696739]
    ];

    // ==== 速度：m/s。3.0 -> 10.8 km/h；3.15 -> 11.3 km/h（贴近历史配速）====
    var SPEED = 3.0;

    var MLAT = 111320.0, MLON = 111320.0 * Math.cos(22.683 * Math.PI / 180.0);
    function dist(a, b) {
        var dy = (b[0] - a[0]) * MLAT, dx = (b[1] - a[1]) * MLON;
        return Math.sqrt(dx * dx + dy * dy);
    }
    var cum = [0], tot = 0;
    for (var i = 0; i < V.length; i++) { tot += dist(V[i], V[(i + 1) % V.length]); cum.push(tot); }
    var T0 = Date.now();

    function cur() {
        var t = ((Date.now() - T0) / 1000.0 * SPEED) % tot;
        var i = 0;
        while (i < V.length - 1 && t > cum[i + 1]) i++;
        var a = V[i], b = V[(i + 1) % V.length];
        var L = dist(a, b);
        var f = L > 0 ? (t - cum[i]) / L : 0;
        var dy = (b[0] - a[0]) * MLAT, dx = (b[1] - a[1]) * MLON;
        var brg = (Math.atan2(dx, dy) * 180.0 / Math.PI + 360) % 360;
        return { lat: a[0] + (b[0] - a[0]) * f, lon: a[1] + (b[1] - a[1]) * f, brg: brg };
    }

    console.log("ROUTE total=" + tot.toFixed(1) + "m speed=" + SPEED + "m/s (= " + (SPEED * 3.6).toFixed(1) + "km/h)");

    // ---- 1) 改写高德定位结果 ----
    try {
        var A = Java.use("com.amap.api.location.AMapLocation");
        function wrapGet(name, fn) {
            var o = A[name];
            o.implementation = function () { try { return fn.call(this); } catch (e) { return o.call(this); } };
        }
        wrapGet("getLatitude", function () { return cur().lat; });
        wrapGet("getLongitude", function () { return cur().lon; });
        wrapGet("getAccuracy", function () { return 5.0; });
        wrapGet("getSpeed", function () { return SPEED; });
        wrapGet("getBearing", function () { return cur().brg; });
        wrapGet("getErrorCode", function () { return 0; });
        wrapGet("getErrorInfo", function () { return ""; });
        wrapGet("getLocationType", function () { return 1; });
        wrapGet("getProvider", function () { return "gps"; });
        wrapGet("getSatellites", function () { return 12; });
        wrapGet("getTime", function () { return Date.now(); });
        wrapGet("getAltitude", function () { return 30.0; });
        wrapGet("getTrustedLevel", function () { return 1; });
        console.log("AMAP overrides installed");
    } catch (e) { console.log("AMAP override fail " + e); }

    // ---- 2) 顺手把系统 Location 也改掉，并对齐防作弊字段 ----
    try {
        var L = Java.use("android.location.Location");
        var seen = 0;
        var gl = L.getLatitude;
        gl.implementation = function () {
            seen++;
            var c = cur();
            if (seen % 50 == 1) console.log("LOC n=" + seen + " -> " + c.lat.toFixed(6) + "," + c.lon.toFixed(6));
            return c.lat;
        };
        L.getLongitude.implementation = function () { return cur().lon; };
        L.getSpeed.implementation = function () { return SPEED; };
        L.isFromMockProvider.implementation = function () { return false; };
        L.hasSpeed.implementation = function () { return true; };
        console.log("LOC overrides installed");
    } catch (e) { console.log("LOC override fail " + e); }
});
