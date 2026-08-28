# 简历导出指南

## 推荐组合

- **投递主用**：docx（HR 直接收的格式）+ pdf（最终版本，防排版错乱）
- **备份**：md（自己迭代用、放 GitHub）

## docx 导出（默认）

调用 docx skill。模板优先级：
1. 用户提供模板 → 用用户的
2. `assets/resume_template.docx` 存在 → 用本 skill 的
3. 都没有 → 用 docx skill 的默认样式（注意控制字体、行距、margin）

样式参数（推荐默认）：
- 中文字体：思源宋体 / 宋体 / 微软雅黑（HR 电脑大概率有）
- 英文字体：Arial / Helvetica / Calibri
- 字号：正文 10.5~11pt，标题 12~14pt，姓名 16~18pt
- 行距：1.15~1.3
- 页边距：上下 1.5cm，左右 1.8cm
- 颜色：通体黑色 + 一个低饱和度强调色（深蓝 / 深灰）

## pdf 导出

**推荐**：docx → libreoffice headless 转 pdf

```bash
libreoffice --headless --convert-to pdf <input.docx> --outdir <out_dir>
```

**不推荐**：直接用 reportlab / weasyprint 从头画，效果丑且容易踩字体坑。

## markdown 导出

最简单直接：文件名建议 `resume_<姓名拼音>_<YYYYMM>.md`，例如 `resume_zhangsan_202605.md`。

## 文件命名建议

投递时的文件名极其重要（很多 HR 直接按文件名搜）：

`<姓名>_<目标岗位>_<X 年经验>.<ext>`

例：`张三_高级产品经理_5年.pdf`

不要叫 `final.pdf` `final_v2.pdf` `修改版.docx`，HR 会觉得你不专业。

## 元数据清理（pdf）

调用 pdf skill 清理 metadata（作者、创建工具），避免泄露原始 word 模板的来源（比如某些模板会留下"WPS 简历模板 v3.2"字样）。

## 隐私 & 安全

- 简历**默认不写身份证号、家庭住址、紧急联系人**
- 投行 / 公务员 / 国企等特殊岗位另外要求时再补
- 如果用户上传的简历里有这些，导出新版本时**主动删除并提示用户**
