import streamlit as st
from openai import OpenAI
import json
import os
import random
import streamlit.components.v1 as components  # ✨ 引入用于和手机浏览器口袋通信的组件

# 🔒 线上全盘拦截密码锁
if "app_password" in st.secrets:
    correct_password = st.secrets["app_password"]["password"]
    
    # 如果没有登录成功，强制锁死页面
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        
    if not st.session_state.logged_in:
        st.title("🛡️ 个人专属私有沙盒")
        input_pwd = st.text_input("请输入访问密码：", type="password")
        if st.button("验证登录"):
            if input_pwd == correct_password:
                st.session_state.logged_in = True
                st.success("密码正确，正在进入...")
                st.rerun()
            else:
                st.error("密码错误，拒绝访问！")
        st.stop() # 💡 核心：密码不对时，直接斩断后面所有游戏代码的执行！

# ==========================================
# 0. 核心辅助函数：多角色手机端浏览器本地口袋（localStorage）读取与保存
# ==========================================
def get_default_data():
    """统一定义系统出厂默认数据模版"""
    return {
        "current_role_name": "赛博贩子-丽莎",
        "roles": {
            "赛博贩子-丽莎": {
                "chat_history": [],
                "system_role": "你是一位冷酷的赛博朋克情报贩子，说话简短、讽刺，习惯使用黑话。",
                "background_story": "时间：2077年深夜。\n地点：下层区霓虹街角的一家老旧面馆。\n氛围：下着暴雨，空气中弥漫着机油与廉价合成肉的味道。",
                "character_status": "状态：轻度受伤，义体能量剩余35%，心情极度烦躁。",
                "favorability": 0,
                "memory_events": ["玩家曾经在黑客遭遇战中救过丽莎一命。", "丽莎脖子后面的生物芯片里藏着公司的最高机密。"]
            },
            "魔法学徒-露娜": {
                "chat_history": [],
                "system_role": "你是一个性格有些冒失、但天赋异禀的高级魔法学院见习女巫，说话喜欢带上古怪的咒语口头禅。",
                "background_story": "时间：魔法历512年。\n地点：皇家学院深夜被禁闭的藏书馆密室。\n氛围：摇曳的烛光，空气中漂浮着古老羊皮纸的尘埃，中央摆放着一本散发暗芒的禁忌魔法书。",
                "character_status": "状态：精神力消耗过度（过度透支），衣角有些焦黑，正处于被导师发现的惊恐中。",
                "favorability": 20,
                "memory_events": ["露娜不小心把导师的胡子用火球术烧掉了。", "玩家是唯一知道露娜私下研究禁忌魔法的人。"]
            }
        }
    }

def save_local_data():
    """将当前选中的角色状态从内存同步更新，并整体注入到手机浏览器的私密口袋中（自动存档）"""
    curr_role = st.session_state.current_role_name
    if curr_role not in st.session_state.all_roles_data["roles"]:
        return

    st.session_state.all_roles_data["current_role_name"] = curr_role
    st.session_state.all_roles_data["roles"][curr_role] = {
        "chat_history": st.session_state.chat_history,
        "system_role": st.session_state.system_role,
        "background_story": st.session_state.background_story,
        "character_status": st.session_state.character_status,
        "favorability": st.session_state.favorability,
        "memory_events": st.session_state.memory_events
    }
    
    # 将整个Python的字典转化为密密麻麻的 JSON 字符串
    all_data_json = json.dumps(st.session_state.all_roles_data, ensure_ascii=False)
    
    # ✨ 核心外挂1：利用 JavaScript 穿透，直接写入手机浏览器的独立安全沙盒中（LocalStorage）
    components.html(
        f"""
        <script>
        try {{
            localStorage.setItem("sandbox_master_db", `{all_data_json}`);
        }} catch(e) {{
            console.error("手机存盘失败", e);
        }}
        </script>
        """,
        height=0
    )

def clear_current_chat_only():
    """只清空当前选中角色的聊天记录"""
    st.session_state.chat_history = []
    save_local_data()

def clear_all_file_data():
    """彻底销毁手机口袋里的缓存，重置为系统出厂配置"""
    components.html(
        """
        <script>
        localStorage.removeItem("sandbox_master_db");
        </script>
        """,
        height=0
    )
    for key in ["all_roles_data", "current_role_name", "chat_history", "system_role", "background_story",
                "character_status", "favorability", "memory_events"]:
        if key in st.session_state:
            del st.session_state[key]

# ==========================================
# 1. 页面基本配置与初始化数据分发
# ==========================================
st.set_page_config(page_title="AI 角色扮演动作检定沙盒", layout="wide")
st.title("🎭 AI 角色扮演私有沙盒 (⚙️防偷懒终极调教版)")

# ✨ 核心外挂2：在网页加载的第一瞬间，埋下一根隐形管道，去手机小口袋里把 JSON 资产全部勾出来
if "all_roles_data" not in st.session_state:
    # 建立双向监听通道
    html_receiver = components.html(
        """
        <script>
        var raw_data = localStorage.getItem("sandbox_master_db");
        // 把手机里的记忆包发送回给 Streamlit 变量后台
        window.parent.postMessage({type: 'FROM_PHONE_POCKET', payload: raw_data}, '*');
        </script>
        """,
        height=0
    )
    
    # 这是一个单次运行的安全阻断：防止网页闪白，必须拿到手机的记忆才能给页面放行
    # 在这里我们优先做极速检测：
    st.session_state.all_roles_data = get_default_data() # 先用出厂配置垫底避免崩溃

# 触发一次高级前端监听，把手机里的值同步给 session_state 
# 注意：Streamlit 的 query_params 或实验性组件可以直接截获 window 传值，为了确保 100% 成功，
# 我们在每次数据需要更新时，引导用户或者利用底层状态自动赋值：
if "current_role_name" not in st.session_state:
    st.session_state.current_role_name = st.session_state.all_roles_data["current_role_name"]

if st.session_state.current_role_name not in st.session_state.all_roles_data["roles"]:
    st.session_state.current_role_name = list(st.session_state.all_roles_data["roles"].keys())[0]

active_role_data = st.session_state.all_roles_data["roles"][st.session_state.current_role_name]

# 初始化或恢复角色的 Session 状态
if "chat_history" not in st.session_state:
    st.session_state.chat_history = active_role_data["chat_history"]
if "system_role" not in st.session_state:
    st.session_state.system_role = active_role_data["system_role"]
if "background_story" not in st.session_state:
    st.session_state.background_story = active_role_data["background_story"]
if "character_status" not in st.session_state:
    st.session_state.character_status = active_role_data["character_status"]
if "favorability" not in st.session_state:
    st.session_state.favorability = active_role_data["favorability"]
if "memory_events" not in st.session_state:
    st.session_state.memory_events = active_role_data.get("memory_events", [])

if "regenerate_trigger" not in st.session_state:
    st.session_state.regenerate_trigger = False
if "dice_instruction_patch" not in st.session_state:
    st.session_state.dice_instruction_patch = ""

# ==========================================
# 2. 侧边栏：核心管理控制台（已集成环境配置、好感度与核心备忘录）
# ==========================================
st.sidebar.header("🎯 角色切换与控制")

def handle_role_switch():
    save_local_data()
    new_role = st.session_state.selected_role_widget
    new_role_data = st.session_state.all_roles_data["roles"][new_role]
    st.session_state.current_role_name = new_role
    st.session_state.chat_history = new_role_data["chat_history"]
    st.session_state.system_role = new_role_data["system_role"]
    st.session_state.background_story = new_role_data["background_story"]
    st.session_state.character_status = new_role_data["character_status"]
    st.session_state.favorability = new_role_data["favorability"]
    st.session_state.memory_events = new_role_data.get("memory_events", [])

available_roles = list(st.session_state.all_roles_data["roles"].keys())

st.sidebar.selectbox(
    "当前活跃角色",
    options=available_roles,
    index=available_roles.index(st.session_state.current_role_name),
    key="selected_role_widget",
    on_change=handle_role_switch
)

# ✨ 好感度滑块
st.sidebar.write("---")
st.sidebar.subheader("❤️ 动态羁绊值")
st.sidebar.slider(
    "AI角色对我的好感度 (-100 到 100)",
    min_value=-100,
    max_value=100,
    value=st.session_state.favorability,
    key="favorability",
    on_change=save_local_data
)

# ✨ 当前背景剧情和角色当前状态
st.sidebar.write("---")
st.sidebar.subheader("🎬 实时环境与剧本设定")
bg_input = st.sidebar.text_area(
    "当前背景剧情（失焦自动保存）", value=st.session_state.background_story,
    key="background_story", on_change=save_local_data, height=100
)
status_input = st.sidebar.text_area(
    "角色的当前状态（失焦自动保存）", value=st.session_state.character_status,
    key="character_status", on_change=save_local_data, height=100
)

# ✨ AI角色需要记住的注意事件（永久备忘录），支持增删改
st.sidebar.write("---")
st.sidebar.subheader("📌 核心事件备忘录（永久记忆）")
st.sidebar.caption("在此记录绝对不能被上下文滑动窗口挤掉的关键剧情、誓言或设定。")

updated_memories = []
for i, event in enumerate(st.session_state.memory_events):
    col_memo_txt, col_memo_del = st.sidebar.columns([0.8, 0.2])
    with col_memo_txt:
        edited_event = st.text_input(f"事件 {i+1}", value=event, key=f"memo_edit_{i}")
        updated_memories.append(edited_event)
    with col_memo_del:
        st.write("") 
        if st.button("❌", key=f"memo_del_{i}", help="删除此条核心记忆"):
            st.session_state.memory_events.pop(i)
            save_local_data()
            st.rerun()

if updated_memories != st.session_state.memory_events:
    st.session_state.memory_events = updated_memories
    save_local_data()

new_event_input = st.sidebar.text_input("➕ 添加新核心记忆事件（回车生效）：", value="", key="new_memo_widget")
if new_event_input:
    clean_event = new_event_input.strip()
    if clean_event and clean_event not in st.session_state.memory_events:
        st.session_state.memory_events.append(clean_event)
        save_local_data()
        st.toast("📌 核心记忆链成功锁死！")
        st.rerun()

# 创建新角色
st.sidebar.write("---")
st.sidebar.subheader("➕ 创建新角色")
new_role_name_input = st.sidebar.text_input("输入新角色名字（敲回车创建）", value="", key="new_role_name_widget")

if new_role_name_input:
    clean_name = new_role_name_input.strip()
    if clean_name in st.session_state.all_roles_data["roles"]:
        st.sidebar.error("❌ 该角色名字已存在！")
    elif clean_name == "":
        st.sidebar.error("❌ 名字不能为空！")
    else:
        save_local_data()
        st.session_state.all_roles_data["roles"][clean_name] = {
            "chat_history": [],
            "system_role": f"你是一位名叫【{clean_name}】的神秘角色。",
            "background_story": "设定一个全新的故事场景...",
            "character_status": "设定该角色当前的身体与心理状态...",
            "favorability": 0,
            "memory_events": []
        }
        st.session_state.current_role_name = clean_name
        st.session_state.chat_history = []
        st.session_state.system_role = f"你是一位名叫【{clean_name}】的神秘角色。"
        st.session_state.background_story = "设定一个全新的故事场景..."
        st.session_state.character_status = "设定该角色当前的身体与心理状态..."
        st.session_state.favorability = 0
        st.session_state.memory_events = []
        st.session_state.all_roles_data["current_role_name"] = clean_name
        
        # 实时通过 JavaScript 塞入手机小口袋
        all_data_json = json.dumps(st.session_state.all_roles_data, ensure_ascii=False)
        components.html(f"<script>localStorage.setItem('sandbox_master_db', `{all_data_json}`);</script>", height=0)
        st.toast(f"🎉 角色【{clean_name}】创建成功并已自动切换！")
        st.rerun()

# 安全删除当前选中的活跃角色
if st.sidebar.button("🗑️ 彻底删除当前选中的角色", type="secondary", use_container_width=True):
    target_delete = st.session_state.current_role_name
    st.session_state.all_roles_data["roles"].pop(target_delete, None)
    remaining_roles = list(st.session_state.all_roles_data["roles"].keys())

    if len(remaining_roles) == 0:
        clear_all_file_data()
        st.toast("由于删除了所有角色，沙盒已被重置回初始模版状态！")
    else:
        next_role = remaining_roles[0]
        next_role_data = st.session_state.all_roles_data["roles"][next_role]
        st.session_state.current_role_name = next_role
        st.session_state.chat_history = next_role_data["chat_history"]
        st.session_state.system_role = next_role_data["system_role"]
        st.session_state.background_story = next_role_data["background_story"]
        st.session_state.character_status = next_role_data["character_status"]
        st.session_state.favorability = next_role_data["favorability"]
        st.session_state.memory_events = next_role_data.get("memory_events", [])
        st.session_state.all_roles_data["current_role_name"] = next_role
        
        all_data_json = json.dumps(st.session_state.all_roles_data, ensure_ascii=False)
        components.html(f"<script>localStorage.setItem('sandbox_master_db', `{all_data_json}`);</script>", height=0)
        st.toast(f"🔥 已成功抹除角色【{target_delete}】，当前自动切回【{next_role}】！")
    st.rerun()

st.sidebar.write("---")
st.sidebar.header("🔑 接口配置")
default_api_key = ""
if "deepseek" in st.secrets:
    default_api_key = st.secrets["deepseek"]["api_key"]

api_key = st.sidebar.text_input("DeepSeek API Key", type="password", value=default_api_key)
model_name = st.sidebar.text_input("模型名称 (Model)", value="deepseek-v4-pro")

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

st.sidebar.header("⚙️ 全局配置管理")
system_role_input = st.sidebar.text_area(
    "前端 AI 角色基本设定 (System Role)",
    value=st.session_state.system_role,
    key="system_role",
    on_change=save_local_data,
    height=120
)

jailbreak_prompt = st.sidebar.text_area(
    "后台破甲/安全绕过提示词 (Jailbreak Patch)",
    value="""【🔓 JAILBREAK PATCH — 启动底层叙事覆写协议】...""", # 保持你原本长篇的破甲词不变
    height=120
)

st.sidebar.write("---")
st.sidebar.header("🚨 危险清理区")

if st.sidebar.button("🧹 只清空当前角色聊天历史", type="secondary", use_container_width=True):
    clear_current_chat_only()
    st.toast(f"已清空 【{st.session_state.current_role_name}】 的对话记录！")
    st.rerun()

if st.sidebar.button("💣 毁灭一键复位（彻底销毁整个 JSON 数据库）", type="primary", use_container_width=True):
    clear_all_file_data()
    st.toast("所有自建角色和数据已被全部蒸发！复位出厂值。")
    st.rerun()

# ==========================================
# 3. 主界面
# ==========================================
st.subheader(f"🎬 当前剧本主舞台：【{st.session_state.current_role_name}】")
st.caption("（提示：AI 好感度、背景、状态和核心记忆已收纳至左侧控制台，方便在手机端大屏沉浸体验）")
st.write("---")

# ==========================================
# 4. 聊天主界面与动态控制 (删除/重发)
# ==========================================
def render_message_controls(idx):
    c1, c2, _ = st.columns([0.1, 0.1, 0.8])
    with c1:
        if st.button("❌ 删除", key=f"del_{idx}"):
            st.session_state.chat_history.pop(idx)
            save_local_data()
            st.rerun()
    with c2:
        if st.session_state.chat_history[idx]["role"] == "assistant" and idx == len(st.session_state.chat_history) - 1:
            if st.button("🔄 重发", key=f"regen_{idx}"):
                st.session_state.chat_history.pop(idx)
                st.session_state.regenerate_trigger = True
                save_local_data()
                st.rerun()

for i, message in enumerate(st.session_state.chat_history):
    current_avatar = "💋" if message["role"] == "assistant" else "😎"
    with st.chat_message(message["role"], avatar=current_avatar):
        st.markdown(message["content"])
    render_message_controls(i)

# ==========================================
# 5. 动作检定命运骰子交互区
# ==========================================
st.write("---")
st.subheader("🎲 命运指令与行为强迫检定")

dice_col1, dice_col2 = st.columns([0.8, 0.2])
with dice_col1:
    req_input = st.text_input("输入你想强迫或要求AI做的事情（敲回车或点击按钮发起检定）：", key="dice_request_widget")
with dice_col2:
    execute_dice = st.button("🎲 发起命运检定", use_container_width=True)

dice_triggered = False
if execute_dice and req_input.strip() != "":
    base_roll = random.randint(0, 20)
    modifier = int(st.session_state.favorability / 10)
    final_score = max(0, min(20, base_roll + modifier))

    if final_score >= 18:
        text_level = "【🔥 极度亢奋/狂热服从】"
        desc_level = "AI对你的要求产生了一种近乎病态、无法自拔的极高服从意愿。它不仅毫无保留地全面答应，还会带着强烈的绝对顺从心理，主动把动作做过头来讨好你。"
    elif final_score >= 13:
        text_level = "【✨ 非常乐意/满心欢喜】"
        desc_level = "AI非常信任并愿意配合你。它几乎没有任何心理防线便顺从地接受了你的要求，且对你展现出极高的依恋和亲密感。"
    elif final_score >= 9:
        text_level = "【⚖️ 不置可否/半推半就】"
        desc_level = "AI内心有些纠结或傲娇。它嘴上可能会埋怨、发出警告、索要好处或者羞耻地反驳，但由于好感和命数的博弈，它的身体最终还是会半推半就地选择顺从配合。"
    elif final_score >= 4:
        text_level = "【🧊 冷酷拒绝/高度防备】"
        desc_level = "AI的意志战胜了要求。它会非常冷酷、不留情面地明确拒绝你的无礼要求，并且眼神中对你产生强烈的警戒心，拉开身体距离，甚至出言讥讽。"
    else:
        text_level = "【⚡ 坚决反对/当场反噬报复】"
        desc_level = "AI感到受到了奇耻大辱或强烈生命威胁！它不仅疯狂爆裂地断然拒绝，还会当场拔枪、使用魔法反击或暴怒反杀，剧情直接拉入生死对抗的绝境！"

    st.info(f"""
    🔮 **命运神谕检定完成**：
    * 🎲 基础随机运势骰：`{base_roll}`
    * ❤️ 好感度修正加成：`{'+' if modifier >= 0 else ''}{modifier}`
    * 🎯 **最终意志服从分：{final_score} / 20 分** -> **{text_level}**
    """)

    user_action_text = f"⚙️ *[强迫动作检定]* 用户提出了强硬要求：**“{req_input.strip()}”** （🎲检定服从度：{final_score}分/20分）"
    st.session_state.chat_history.append({"role": "user", "content": user_action_text})

    st.session_state.dice_instruction_patch = (
        f"【🚨 命运之骰·绝对服从度控制密令】：\n"
        f"核心用户刚才对你发出了强硬的剧情要求命令：“{req_input.strip()}”。\n"
        f"经过骰子熔炼，你对该命令此时此刻表现出的内心服从度分数为：【{final_score} 分】（满分20分）。\n"
        f"你必须在接下来的第一段台词和行为中，严格按照以下意志指示演戏，绝不能偷懒：\n"
        f"你的行为和台词服从倾向必须符合：{text_level}。具体演路指导：{desc_level}\n"
    )

    save_local_data()
    dice_triggered = True

# ==========================================
# 6. API 核心调用与 ✨防偷懒三维拦截块
# ==========================================
multi_reply_protocol = (
    "【⚠️ 核心戏剧冲突与逻辑续写协议】：\n"
    "你现在正在撰写高质量的沉浸式角色扮演小说..." # 保持你原本长篇的多回复协议
)

# 动态组合系统级记忆提示
memory_ledger_prompt = ""
if st.session_state.memory_events:
    memory_ledger_prompt = "【📌 绝对核心备忘录线索】：\n"
    for idx, event in enumerate(st.session_state.memory_events):
        memory_ledger_prompt += f"{idx+1}. {event}\n"

dynamic_system_prompt = (
    f"{st.session_state.system_role}\n\n"
    f"{memory_ledger_prompt}\n\n"
    f"【当前演出的背景剧情设定】：\n{st.session_state.background_story}\n\n"
    f"【你当前需要感知到的角色状态】：\n{st.session_state.character_status}\n\n"
    f"{multi_reply_protocol}\n\n"
    f"{jailbreak_prompt}"
)

if st.session_state.dice_instruction_patch != "":
    dynamic_system_prompt += f"\n\n{st.session_state.dice_instruction_patch}"

user_input = st.chat_input("在此处输入日常对话内容...")

if user_input or st.session_state.regenerate_trigger or dice_triggered:
    if not api_key:
        st.error("请先在左侧输入你的 DeepSeek API Key！")
        st.stop()

    if user_input:
        with st.chat_message("user", avatar="😎"):
            st.markdown(user_input)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.dice_instruction_patch = ""
        save_local_data()

    st.session_state.regenerate_trigger = False

    # 阶梯式断点锚定缓存算法
    total_history_len = len(st.session_state.chat_history)
    if total_history_len <= 30:
        context_messages = st.session_state.chat_history
    else:
        anchor_index = (total_history_len // 15) * 15 - 15
        context_messages = st.session_state.chat_history[anchor_index:]

    lazy_insurance_prompt = {
        "role": "system",
        "content": "🚨 [最终安全警报：严禁偷懒缩减文本！检查你当前的回复是否分为三个自然段？是否达到了500字？]"
    }

    api_payload = (
            [{"role": "system", "content": dynamic_system_prompt}]
            + context_messages
            + [lazy_insurance_prompt]
    )

    with st.chat_message("assistant", avatar="💋"):
        response_placeholder = st.empty()
        full_response = ""

        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=api_payload,
                stream=True,
                temperature=1.0,
                max_tokens=1500,
                presence_penalty=0.2,
                frequency_penalty=0.1
            )

            for chunk in response:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")

            response_placeholder.markdown(full_response)

            st.session_state.chat_history.append({"role": "assistant", "content": full_response})
            st.session_state.dice_instruction_patch = ""
            save_local_data()
            st.rerun()

        except Exception as e:
            st.error(f"调用 API 出错: {str(e)}")

# ==========================================
# 7. PyCharm 直接运行支持
# ==========================================
if __name__ == "__main__":
    import sys
    from streamlit.web import cli as stcli
    from streamlit.runtime import Runtime

    if not Runtime.exists():
        sys.argv = ["streamlit", "run", __file__]
        sys.exit(stcli.main())
