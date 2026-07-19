#!/usr/bin/env python3
"""对 inbox 文件做分类：值得入库 vs 不值得入库
基于文件名 + 内容前 20 行的关键词判断
"""
import re
from pathlib import Path

VAULT = Path("/Users/gubin/workspace/gbwikis")
INBOX = VAULT / "raw" / "inbox"

# 不值得入库的关键词模式（生活/通用/时效性/太泛）
SKIP_PATTERNS = [
    # 数学题/教辅
    r"数学|教辅|植树节|错题|图形周长|时针角度|最大公因数|圆周率|自然数|3分之10|a被b除|解答题目|杨奇函|阅读理解|小学",
    # 日常生活
    r"便秘|饮食|芝麻酱|大米|梅花|阅读障碍|儿童|女性缺铁|退休金|公积金|汽车报废|灵活就业|顶尖小学",
    # 购物/产品规格
    r"显示器尺寸|电视机尺寸|iPhone|iPad|kindle.*自己做|树莓派.*价格|小米盒子",
    # 投资/金融（时效性强）
    r"基金.*费率|股票.*沪深|国债|信用债|债券.*组合|基金.*估值|红利|通胀.*国债|网格投资|基金实时",
    # 通用知识（AI 已熟练掌握）
    r"HTTP502|UNPIVOT|VSCode.*大写|python.*协程|sqlite.*db文件|coalesce|OLEDB|Office版本|Nearnextto|besides|CPU核心",
    # 时效性价格/平台
    r"收费|价格|最便宜|云主机.*推荐|试用|OpenRouter.*替代|排名|私有化部署.*价格",
    # 太泛/不明确
    r"询问身份|代码含义|代码格式化|安全问题解释|你的数据什么时候|请提取图中|图片转PDF|图形识别需求|日历提醒|识别英语|翻译",
    # 其他生活
    r"抖音|WSBK|OECD|Cookie功能|恢复ChatGPT|quora.*抱怨|图片识别.*markdown|tikz",
    # 数学/教育 app（非技术）
    r"数学题.*UI|错题.*app|植树节小报",
]

# 值得入库的关键词（技术深度内容）
KEEP_PATTERNS = [
    r"Azure.*B2C|Azure.*ADF|Azure.*存储",
    r"opencode|openclaw|openwiki|ohmyopencode|ohmyopenclient",
    r"agent.*开发|agent.*架构|agent.*设计|Agent.*学习|Agent.*研究",
    r"jboss|weblogic|docker|nextjs|spring|SSIS|VB.*迁移",
    r"CVE|安全.*修复|sql注入|认证证书",
    r"skill|agents\.md|agentsmd",
    r"vercel|deploy|部署",
    r"latex.*tikz|latex.*数学",
    r"latex|FOP|PDF",
    r"prompt|提示词",
    r"API.*调用|事务.*API",
    r"GitHub.*action|workflow",
    r"企业微信.*机器人|微信.*插件",
    r"交易系统|交易.*价格",
    r"IBM i",
    r"hermes|claude.*ignore|tmux|kitty",
    r"架构.*对比|架构.*总结",
    r"superpowers|brainstorming",
    r"mac.*卸载|mac.*终端|macos.*查询|zshrc.*环境变量",
    r"vscode.*git|notepad.*xml|dbeaver|oracle",
    r"Word.*邮件合并|docm|Office.*升级|Office.*删除",
    r"proxyip|warp|linux",
    r"tui.*agent|tui.*终端",
    r"React.*窗口|Node\.js.*项目",
    r"GLM|Claude.*Code|DeepSeek|codex",
    r"React.*窗口",
]

def classify(filename, content_preview):
    """返回 (worth_keeping, reason)"""
    text = filename + " " + content_preview
    
    # 先检查是否匹配"不值得"模式
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return False, f"匹配跳过模式: {pattern}"
    
    # 再检查是否匹配"值得"模式
    for pattern in KEEP_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True, f"匹配保留模式: {pattern}"
    
    # 默认：不确定，倾向跳过
    return False, "未匹配任何保留模式，默认跳过"

def main():
    files = sorted(INBOX.glob("*.md"))
    print(f"总计 {len(files)} 个文件\n")
    
    keep = []
    skip = []
    
    for f in files:
        try:
            content = f.read_text(encoding="utf-8")[:500]
        except Exception:
            content = ""
        
        worth, reason = classify(f.name, content)
        if worth:
            keep.append((f.name, reason))
        else:
            skip.append((f.name, reason))
    
    print(f"=== 值得入库 ({len(keep)} 个) ===")
    for name, reason in keep:
        print(f"  ✓ {name}")
    
    print(f"\n=== 不值得入库 ({len(skip)} 个) ===")
    for name, reason in skip:
        print(f"  ✗ {name}  ({reason})")

if __name__ == "__main__":
    main()
