# 编码配置解码

## 识别信号

1. API 返回有 `_encoded: true` 标志
2. `definition` 字段是 Base64 字符串而非 JSON
3. JS 中有 `atob()`/`btoa()` + `TextEncoder`/`TextDecoder` + XOR
4. Runtime config 中有 `obfuscationKey`

```bash
grep -oE '(atob|btoa|obfuscation|_encoded)' /tmp/*.js | sort | uniq -c
grep -oE 'obfuscationKey:"[^"]*"' /tmp/page.html
```

## 常见方案

### Base64 + XOR

```python
import base64, json

def decode(encoded, key):
    raw = base64.b64decode(encoded)
    key_bytes = key.encode('utf-8')
    decrypted = bytes([raw[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(raw))])
    return json.loads(decrypted.decode('utf-8'))
```

### 短码映射（组件/属性名缩写）

配置中 `C74`/`p29` 代替 `StudioBackground`/`color`。

```bash
grep -oE '(codeToComponent|codeToProp)' /tmp/bundle.js
```

映射表通常是动态生成的——所有名称按字母排序分配 `C{nn}`/`p{nn}` 编号。

## 密钥来源

| 框架 | 位置 |
|------|------|
| Nuxt.js | `public:{obfuscationKey:"..."}` in HTML |
| Next.js | `__NEXT_DATA__` 的 runtimeConfig |
| SPA | bundle 常量或 `window.__CONFIG__` |

## 查找解码函数

```bash
grep -l '_encoded' /tmp/*.js
grep -A3 '_encoded' /tmp/bundle.js
# 模式：if (t._encoded) { return decode(t.definition, key) }
```
