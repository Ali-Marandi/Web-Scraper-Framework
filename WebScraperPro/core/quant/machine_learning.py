
r"""Machine Learning Module for Quantitative Finance.

Implements LSTM, Transformer, NLP Sentiment Analysis, Anomaly Detection,
and Behavioral Finance models from scratch using only numpy, pandas, and scipy.
No sklearn, torch, or tensorflow dependencies.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Tuple, Optional, Any
import warnings
warnings.filterwarnings("ignore")


# ============================================================================
# 1. LSTM Forecaster - Minimal LSTM from scratch with BPTT + Adam
# ============================================================================

class LSTMForecaster:
    """Minimal LSTM network from scratch with numpy. Single-layer LSTM cell with
    forget, input, and output gates. Trained via truncated BPTT with Adam."""

    def __init__(self, input_size=1, hidden_size=32, output_size=1, learning_rate=0.001):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.lr = learning_rate
        s = 0.08
        self.Wx = np.random.randn(4 * hidden_size, input_size) * s
        self.Wh = np.random.randn(4 * hidden_size, hidden_size) * s
        self.b = np.zeros(4 * hidden_size)
        self.Wy = np.random.randn(output_size, hidden_size) * s
        self.by = np.zeros(output_size)
        self._m = [np.zeros_like(p) for p in [self.Wx, self.Wh, self.b, self.Wy, self.by]]
        self._v = [np.zeros_like(p) for p in [self.Wx, self.Wh, self.b, self.Wy, self.by]]
        self._t = 0

    @staticmethod
    def _sig(x):
        return 1.0 / (1.0 + np.exp(-np.clip(x, -20, 20)))

    def _forward(self, seq):
        T = len(seq)
        hs = np.zeros((T + 1, self.hidden_size))
        cs = np.zeros((T + 1, self.hidden_size))
        os_ = np.zeros((T, self.output_size))
        caches = []
        hz = self.hidden_size
        for t in range(T):
            xt = np.atleast_1d(seq[t]).astype(float)
            g = self.Wx @ xt + self.Wh @ hs[t] + self.b
            f = self._sig(g[:hz]); i = self._sig(g[hz:2*hz])
            cb = np.tanh(g[2*hz:3*hz]); o = self._sig(g[3*hz:])
            cs[t+1] = f * cs[t] + i * cb
            hs[t+1] = o * np.tanh(cs[t+1])
            os_[t] = self.Wy @ hs[t+1] + self.by
            caches.append((xt, f, i, cb, o, cs[t], hs[t]))
        return os_, hs, cs, caches

    def _backward(self, seq, caches, os_, hs):
        hz = self.hidden_size
        dWx = np.zeros_like(self.Wx); dWh = np.zeros_like(self.Wh)
        db = np.zeros_like(self.b); dWy = np.zeros_like(self.Wy); dby = np.zeros_like(self.by)
        dh_n = np.zeros(hz); dc_n = np.zeros(hz)
        for t in reversed(range(len(seq))):
            xt, f, i, cb, o, c_prev, h_prev = caches[t]
            dy = os_[t] - np.atleast_1d(seq[min(t+1, len(seq)-1)]).astype(float)
            dWy += np.outer(dy, hs[t+1]); dby += dy
            dh = self.Wy.T @ dy + dh_n
            dc = dh * o * (1 - np.tanh(hs[t+1])**2) + dc_n
            do_ = dh * np.tanh(hs[t+1]); dcb = dc * i; di = dc * cb; df = dc * c_prev
            dinp = np.concatenate([
                df * f * (1 - f), di * i * (1 - i), dcb * (1 - cb**2), do_ * o * (1 - o)])
            dWx += np.outer(dinp, xt); dWh += np.outer(dinp, hs[t]); db += dinp
            dh_n = self.Wh.T @ dinp; dc_n = f * dc
        return [dWx, dWh, db, dWy, dby]

    def _adam_step(self, grads):
        params = [self.Wx, self.Wh, self.b, self.Wy, self.by]
        self._t += 1
        for idx in range(5):
            self._m[idx] = 0.9 * self._m[idx] + 0.1 * grads[idx]
            self._v[idx] = 0.999 * self._v[idx] + 0.001 * grads[idx]**2
            mh = self._m[idx] / (1 - 0.9**self._t)
            vh = self._v[idx] / (1 - 0.999**self._t)
            u = self.lr * mh / (np.sqrt(vh) + 1e-8)
            np.clip(u, -1.0, 1.0, out=u)
            params[idx] -= u
        self.Wx, self.Wh, self.b, self.Wy, self.by = params

    def fit(self, values, epochs=50, seq_length=20, batch_size=32, verbose=False):
        vals = np.array(values, dtype=float)
        losses = []
        for ep in range(epochs):
            el = 0.0; cnt = 0
            n_s = max(1, len(vals) - seq_length)
            perm = np.random.permutation(n_s)
            for idx in perm[:max(1, n_s // batch_size)]:
                end = min(idx + seq_length + 1, len(vals))
                seq = vals[idx:end]
                if len(seq) < seq_length + 1: continue
                try:
                    os_, hs, cs, ca = self._forward(seq)
                    loss = np.mean((os_ - np.atleast_1d(seq[1:]).astype(float))**2)
                    grads = self._backward(seq, ca, os_, hs)
                    self._adam_step(grads)
                    el += loss; cnt += 1
                except Exception: continue
            losses.append(el / max(cnt, 1))
            if verbose and (ep+1) % 10 == 0:
                print(f"  Epoch {ep+1}/{epochs}, Loss: {losses[-1]:.6f}")
        return {"losses": losses, "final_loss": losses[-1] if losses else None}

    def predict(self, values, n_steps=10):
        vals = np.array(values, dtype=float)
        seq = vals.copy()
        preds = []
        for _ in range(n_steps):
            x_t = np.atleast_1d(seq[-1]).astype(float)
            h_t = np.zeros(self.hidden_size); c_t = np.zeros(self.hidden_size)
            for j in range(max(1, len(seq)-1), len(seq)):
                inp = self.Wx @ np.atleast_1d(seq[j]).astype(float) + self.Wh @ h_t + self.b
                f = self._sig(inp[:self.hidden_size])
                i = self._sig(inp[self.hidden_size:2*self.hidden_size])
                cb = np.tanh(inp[2*self.hidden_size:3*self.hidden_size])
                o = self._sig(inp[3*self.hidden_size:])
                c_t = f * c_t + i * cb; h_t = o * np.tanh(c_t)
            pred = float(self.Wy @ h_t + self.by)
            preds.append(pred); seq = np.append(seq, pred)
        return {"predictions": preds, "n_steps": n_steps}


class TransformerForecaster:
    """Minimal Transformer with multi-head self-attention from scratch with numpy."""

    def __init__(self, d_model=32, n_heads=4, n_layers=2, learning_rate=0.001, d_ff=64):
        self.d_model = d_model; self.n_heads = n_heads
        self.n_layers = n_layers; self.d_ff = d_ff; self.d_k = d_model // n_heads
        self.lr = learning_rate
        s = 0.05
        self.Wq = [np.random.randn(d_model, d_model)*s for _ in range(n_layers)]
        self.Wk = [np.random.randn(d_model, d_model)*s for _ in range(n_layers)]
        self.Wv = [np.random.randn(d_model, d_model)*s for _ in range(n_layers)]
        self.Wo = [np.random.randn(d_model, d_model)*s for _ in range(n_layers)]
        self.W1 = [np.random.randn(d_model, d_ff)*s for _ in range(n_layers)]
        self.W2 = [np.random.randn(d_ff, d_model)*s for _ in range(n_layers)]
        self.b1l = [np.zeros(d_ff) for _ in range(n_layers)]
        self.b2l = [np.zeros(d_model) for _ in range(n_layers)]
        self.W_out = np.random.randn(d_model, 1) * s; self.b_out = np.zeros(1)
        self.gammas = [np.ones(d_model) for _ in range(n_layers*2)]
        self.betas = [np.zeros(d_model) for _ in range(n_layers*2)]

    def _ln(self, x, g, b):
        m = np.mean(x, axis=-1, keepdims=True)
        return g * (x - m) / np.sqrt(np.var(x, axis=-1, keepdims=True) + 1e-6) + b

    def _sm(self, x, a=-1):
        e = np.exp(x - np.max(x, axis=a, keepdims=True))
        return e / np.sum(e, axis=a, keepdims=True)

    def _pe(self, sl):
        p = np.zeros((sl, self.d_model))
        for pos in range(sl):
            for i in range(0, self.d_model, 2):
                p[pos, i] = np.sin(pos / (10000**(i/self.d_model)))
                if i+1 < self.d_model:
                    p[pos, i+1] = np.cos(pos / (10000**(i/self.d_model)))
        return p

    def _forward(self, x):
        sl = x.shape[0]; h = x + self._pe(sl)
        for l in range(self.n_layers):
            hn = self._ln(h, self.gammas[l*2], self.betas[l*2])
            Q = hn @ self.Wq[l]; K = hn @ self.Wk[l]; V = hn @ self.Wv[l]
            heads = []
            for i in range(self.n_heads):
                sc = Q[:, i*self.d_k:(i+1)*self.d_k] @ K[:, i*self.d_k:(i+1)*self.d_k].T / np.sqrt(self.d_k)
                heads.append(self._sm(sc) @ V[:, i*self.d_k:(i+1)*self.d_k])
            ao = np.concatenate(heads, axis=-1) @ self.Wo[l]; h = h + ao
            hn2 = self._ln(h, self.gammas[l*2+1], self.betas[l*2+1])
            ff = np.maximum(0, hn2 @ self.W1[l] + self.b1l[l]) @ self.W2[l] + self.b2l[l]
            h = h + ff
        return (h @ self.W_out + self.b_out).flatten()

    def fit(self, values, epochs=50, seq_length=32, verbose=False):
        vals = np.array(values, dtype=float)
        mv, sv = np.mean(vals), max(np.std(vals), 1e-8)
        vn = (vals - mv) / sv; losses = []; sl = seq_length
        for ep in range(epochs):
            el = 0.0; cnt = 0
            ns = max(1, len(vn) - sl)
            for idx in np.random.permutation(ns)[:min(16, ns)]:
                x = np.repeat(vn[idx:idx+sl].reshape(-1,1), self.d_model, axis=1)
                try:
                    pred = self._forward(x); tgt = vn[idx+sl]; loss = (pred[0]-tgt)**2
                    g = 2*(pred[0]-tgt)
                    self.W_out -= self.lr * g * x[-1].reshape(-1,1); self.b_out -= self.lr * g
                    el += loss; cnt += 1
                except Exception: continue
            losses.append(el / max(cnt, 1))
            if verbose and (ep+1) % 10 == 0:
                print(f"  Epoch {ep+1}/{epochs}, Loss: {losses[-1]:.6f}")
        self._mv = mv; self._sv = sv
        return {"losses": losses, "final_loss": losses[-1] if losses else None}

    def predict(self, values, n_steps=10):
        vals = list(values); mv = getattr(self, '_mv', np.mean(vals))
        sv = getattr(self, '_sv', max(np.std(vals), 1e-8)); preds = []
        for _ in range(n_steps):
            r = np.array(vals[-self.d_model:]); n = (r-mv)/sv
            x = np.repeat(n.reshape(-1,1), self.d_model, axis=1)
            try: pred = self._forward(x)[0] * sv + mv
            except Exception: pred = vals[-1]
            preds.append(float(pred)); vals.append(pred)
        return {"predictions": preds, "n_steps": n_steps}


# ============================================================================
# 3. NLP Sentiment Analyzer (Persian + English)
# ============================================================================

class NLPSentimentAnalyzer:
    """Lexicon-based sentiment for Persian and English financial text."""

    PERSIAN_WORDS = {
        'رشد': 1.0, 'افزایش': 0.9, 'سود': 0.8, 'موفقیت': 1.0, 'بهبود': 0.9,
        'صعود': 1.0, 'صادرات': 0.7, 'تولید': 0.5, 'مثبت': 0.8, 'بهترین': 1.0,
        'رونق': 0.9, 'قوی': 0.7, 'پیشرفت': 0.8, 'بهره‌وری': 0.7, 'پایدار': 0.5,
        'مطلوب': 0.7, 'بازده': 0.6, 'فرصت': 0.7, 'مزیت': 0.7, 'صعودی': 1.0,
        'عرضه': 0.3, 'تقاضا': 0.4, 'سرمایه‌گذاری': 0.6, 'منطقه': 0.1,
        'کاهش': -0.8, 'نزول': -0.9, 'سقوط': -1.0, 'بحران': -1.0, 'تورم': -0.7,
        'ضرر': -1.0, 'بیکاری': -0.8, 'تحریم': -0.9, 'ورشکستگی': -1.0,
        'منفی': -0.8, 'بدترین': -1.0, 'رکود': -0.9, 'ضعیف': -0.7,
        'عقب‌ماندگی': -0.8, 'نامطمئن': -0.6, 'نامطلوب': -0.7, 'ریسک': -0.5,
        'تهدید': -0.7, 'نزولی': -1.0, 'توقف': -0.5, 'محدودیت': -0.4,
        'عدم': -0.2, 'نوسان': -0.4, 'نقدینگی': 0.4, 'بازار': 0.1,
        'سرمایه': 0.3, 'نرخ': 0.0, 'ارزش': 0.3, 'قیمت': 0.0,
    }

    ENGLISH_WORDS = {
        'growth': 1.0, 'increase': 0.9, 'profit': 0.8, 'success': 1.0,
        'improvement': 0.9, 'surge': 1.0, 'export': 0.7, 'production': 0.5,
        'positive': 0.8, 'best': 1.0, 'boom': 0.9, 'strong': 0.7,
        'progress': 0.8, 'productivity': 0.7, 'stable': 0.5, 'favorable': 0.7,
        'yield': 0.6, 'opportunity': 0.7, 'advantage': 0.7, 'bullish': 1.0,
        'rally': 0.9, 'dividend': 0.6, 'upgrade': 0.8, 'innovation': 0.7,
        'decline': -0.8, 'drop': -0.9, 'crash': -1.0, 'crisis': -1.0,
        'inflation': -0.7, 'loss': -1.0, 'unemployment': -0.8, 'bankruptcy': -1.0,
        'negative': -0.8, 'worst': -1.0, 'recession': -0.9, 'weak': -0.7,
        'uncertain': -0.6, 'unfavorable': -0.7, 'risk': -0.5, 'threat': -0.7,
        'bearish': -1.0, 'sell-off': -0.9, 'default': -0.9, 'downgrade': -0.8,
        'sanctions': -0.9, 'debt': -0.5, 'stagnation': -0.8, 'volatility': -0.4,
    }

    NEGATIONS_EN = {'not', 'no', 'never', 'neither', 'nor', 'hardly', 'barely'}
    NEGATIONS_FA = {'نه', 'نا', 'بی', 'بدون', 'عدم', 'نمی'}

    def __init__(self):
        pass

    def _is_persian(self, text):
        persian_chars = set('ابتثجحخدذرزژسشصضطظعغفقکگلمنهوی')
        return sum(1 for c in text if c in persian_chars) > len(text) * 0.2

    def analyze(self, text: str) -> Dict[str, Any]:
        is_fa = self._is_persian(text)
        words_dict = self.PERSIAN_WORDS if is_fa else self.ENGLISH_WORDS
        negations = self.NEGATIONS_FA if is_fa else self.NEGATIONS_EN
        tokens = text.lower().split() if not is_fa else text.split()
        score = 0.0; hits = []; negate = False
        for tok in tokens:
            if tok in negations:
                negate = True; continue
            if tok in words_dict:
                w = words_dict[tok]
                if negate: w = -w * 0.7; negate = False
                score += w; hits.append((tok, w))
        n_words = max(len(tokens), 1)
        norm_score = score / n_words
        label = 'positive' if norm_score > 0.05 else ('negative' if norm_score < -0.05 else 'neutral')
        return {"score": round(norm_score, 4), "magnitude": round(abs(norm_score), 4),
                "label": label, "keyword_hits": hits, "language": "persian" if is_fa else "english"}

    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        return [self.analyze(t) for t in texts]


# ============================================================================
# 4. Anomaly Detector
# ============================================================================

class AnomalyDetector:
    """Multi-method anomaly and structural break detection from scratch."""

    def __init__(self, method='zscore'):
        self.method = method

    def detect(self, values, threshold=3.0, method=None):
        m = method or self.method
        vals = np.array(values, dtype=float)
        n = len(vals); anomalies = []
        if m == 'zscore':
            z = (vals - np.mean(vals)) / max(np.std(vals), 1e-10)
            for i in range(n):
                if abs(z[i]) > threshold:
                    anomalies.append((i, vals[i], float(z[i])))
        elif m == 'iqr':
            q1, q3 = np.percentile(vals, [25, 75])
            iqr = q3 - q1
            lo, hi = q1 - threshold*iqr, q3 + threshold*iqr
            for i in range(n):
                if vals[i] < lo or vals[i] > hi:
                    sc = max(abs(vals[i]-lo), abs(vals[i]-hi)) / max(iqr, 1e-10)
                    anomalies.append((i, vals[i], float(sc)))
        elif m == 'mad':
            med = np.median(vals); mad = np.median(np.abs(vals - med))
            for i in range(n):
                if mad > 0 and abs(vals[i]-med) / (mad * 1.4826) > threshold:
                    anomalies.append((i, vals[i], float(abs(vals[i]-med)/(mad*1.4826))))
        elif m == 'grubbs':
            for _ in range(min(10, n//3)):
                if len(vals) < 3: break
                g = np.max(np.abs(vals - np.mean(vals))) / np.std(vals)
                gc = stats.t.ppf(1-0.05/(2*len(vals)), len(vals)-2)
                crit = gc * np.sqrt((len(vals)-1) / (gc**2 + len(vals)-2))
                if g > crit:
                    idx = np.argmax(np.abs(vals - np.mean(vals)))
                    anomalies.append((int(idx), float(vals[idx]), float(g)))
                    vals = np.delete(vals, idx)
                else: break
        elif m == 'kde':
            try:
                kde = stats.gaussian_kde(vals)
                probs = kde(vals)
                thresh_p = np.percentile(probs, threshold)
                for i in range(n):
                    if probs[i] < thresh_p:
                        anomalies.append((i, vals[i], float(-np.log(max(probs[i], 1e-10)))))
            except Exception:
                pass
        return {"anomalies": anomalies, "anomaly_indices": [a[0] for a in anomalies],
                "method": m, "n_detected": len(anomalies),
                "summary": f"{len(anomalies)} anomalies detected using {m} method"}

    def detect_structural_breaks(self, values, n_breaks=3):
        vals = np.array(values, dtype=float)
        n = len(vals); breaks = []
        for _ in range(n_breaks):
            best_f = -np.inf; best_idx = -1
            for k in range(max(10, n//10), n - max(10, n//10)):
                s1, s2 = vals[:k], vals[k:]
                if len(s1) < 5 or len(s2) < 5: continue
                m1, m2 = np.mean(s1), np.mean(s2)
                v1, v2 = np.var(s1), np.var(s2)
                rss_full = np.sum((vals - np.mean(vals))**2)
                rss_split = np.sum((s1-m1)**2) + np.sum((s2-m2)**2)
                n1, n2 = len(s1), len(s2)
                f_stat = ((rss_full - rss_split) / 1) / max((rss_split / (n-2)), 1e-10)
                if f_stat > best_f:
                    best_f = f_stat; best_idx = k
            if best_idx > 0:
                p_val = 1 - stats.f.cdf(best_f, 1, n-2)
                breaks.append((best_idx, float(vals[best_idx]), float(best_f), float(p_val)))
                vals = np.concatenate([vals[:best_idx], vals[best_idx:]])
            else: break
        return {"breaks": breaks, "n_breaks": len(breaks),
                "summary": f"{len(breaks)} structural breaks detected (Chow test)"}


# ============================================================================
# 5. Behavioral Finance
# ============================================================================

class BehavioralFinance:
    """Kahneman-Tversky prospect theory and behavioral biases."""

    def prospect_theory_value(self, gains_losses, alpha=0.88, lam=2.25, beta=0.88):
        vals = np.array(gains_losses, dtype=float)
        v = np.where(vals >= 0, vals**alpha, -lam * ((-vals)**beta))
        return {"values": v.tolist(), "parameters": {"alpha": alpha, "lambda": lam, "beta": beta},
                "total_value": float(np.sum(v))}

    def loss_aversion_ratio(self, returns):
        r = np.array(returns, dtype=float)
        gains = r[r > 0]; losses = r[r < 0]
        if len(gains) < 2 or len(losses) < 2: return {"ratio": 2.25, "method": "default"}
        return {"ratio": float(abs(np.mean(losses)) / max(abs(np.mean(gains)), 1e-10)),
                "mean_gain": float(np.mean(gains)), "mean_loss": float(np.mean(losses)),
                "method": "empirical"}

    def disposition_effect(self, realized_gains, realized_losses, paper_gains, paper_losses):
        rg = np.sum(realized_gains); rl = np.sum(realized_losses)
        pg = np.sum(paper_gains); pl = np.sum(paper_losses)
        pgr = rg / max(rg+pg, 1e-10)
        plr = abs(rl) / max(abs(rl)+abs(pl), 1e-10)
        de = pgr - plr
        return {"disposition_effect": float(de), "pgr": float(pgr), "plr": float(plr),
                "realized_gains": float(rg), "realized_losses": float(rl),
                "paper_gains": float(pg), "paper_losses": float(pl),
                "interpretation": "Strong disposition bias" if de > 0.2 else "Mild" if de > 0 else "None"}

    def overconfidence_index(self, trade_freq, hit_rate, market_hit_rate):
        diff = hit_rate - market_hit_rate
        conf = trade_freq * max(diff, 0)
        return {"overconfidence_index": float(conf), "trade_frequency": float(trade_freq),
                "hit_rate": float(hit_rate), "market_hit_rate": float(market_hit_rate),
                "interpretation": "High overconfidence" if conf > 10 else "Moderate" if conf > 3 else "Low"}
