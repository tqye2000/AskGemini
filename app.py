###########################################################################
# Interface to Google Gemini Models
#
# History
# When      | Who            | What
# 19/12/2023| Tian-Qing Ye   | Created
# 15/03/2025| Tian-Qing Ye   | Updated to support Gemini 2.0 flash Exp model
# 16/03/2025| Tian-Qing Ye   | Further updated
# 26/03/2025| Tian-Qing Ye   | Add 2.5 Pro
# 19/11/2025| Tian-Qing Ye   | Add 3.0 Pro
############################################################################
import streamlit as st
from streamlit import runtime
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit_javascript import st_javascript
import streamlit_authenticator as stauth
import requests

import os
import sys
from datetime import datetime
from typing import List
import random, string
from base64 import b64decode
import yaml
from yaml.loader import SafeLoader
from PIL import Image
from io import BytesIO
from gtts import gTTS, gTTSError
from langdetect import detect

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

import libs

from google import genai
from google.genai import types

VALID_USERS = st.secrets["valid_users"].split(',')
TEXT2IMG_ENABLES = st.secrets["txt2img_enabled"]
TOTAL_TRIALS = int(st.secrets["total_trials"])
MAX_MESSAGES = int(st.secrets["max_cached_messages"])

class Locale:    
    ai_role_options: List[str]
    ai_role_prefix: str
    ai_role_postfix: str
    title: str
    choose_language: str
    language: str
    lang_code: str
    chat_messages: str
    chat_placeholder: str
    chat_run_btn: str
    chat_clear_btn: str
    clear_doc_btn: str
    enable_search_label: str
    chat_save_btn: str
    file_upload_label: str
    temperature_label: str
    login_prompt: str
    logout_prompt: str
    username_prompt: str
    password_prompt: str
    choose_llm_prompt: str
    support_message: str
    select_placeholder2: str
    stt_placeholder: str
    radio_placeholder: str
    radio_text1: str
    radio_text2: str
    
    def __init__(self, 
                ai_role_options, 
                ai_role_prefix,
                ai_role_postfix,
                title,
                choose_language,
                language,
                lang_code,
                chat_messages,
                chat_placeholder,
                chat_run_btn,
                chat_clear_btn,
                clear_doc_btn,
                enable_search_label,
                chat_save_btn,
                file_upload_label,
                temperature_label,
                login_prompt,
                logout_prompt,
                username_prompt,
                password_prompt,
                choose_llm_prompt,
                support_message,
                select_placeholder2,
                stt_placeholder,
                radio_placeholder,
                radio_text1,
                radio_text2,                
                ):
        self.ai_role_options = ai_role_options, 
        self.ai_role_prefix= ai_role_prefix,
        self.ai_role_postfix= ai_role_postfix,
        self.title= title,
        self.choose_language = choose_language,
        self.language= language,
        self.lang_code= lang_code,
        self.chat_placeholder= chat_placeholder,
        self.chat_messages = chat_messages,
        self.chat_run_btn= chat_run_btn,
        self.chat_clear_btn= chat_clear_btn,
        self.clear_doc_btn = clear_doc_btn,
        self.enable_search_label = enable_search_label,
        self.chat_save_btn= chat_save_btn,
        self.file_upload_label = file_upload_label,
        self.temperature_label = temperature_label,
        self.login_prompt= login_prompt,
        self.logout_prompt= logout_prompt,
        self.username_prompt= username_prompt,
        self.password_prompt= password_prompt,
        self.choose_llm_prompt = choose_llm_prompt,
        self.support_message = support_message,
        self.select_placeholder2= select_placeholder2,
        self.stt_placeholder = stt_placeholder,
        self.radio_placeholder= radio_placeholder,
        self.radio_text1= radio_text1,
        self.radio_text2= radio_text2,


AI_ROLE_OPTIONS_EN = [
    "helpful assistant",
    "code assistant",
    "code reviewer",
    "text improver",
    "cinema expert",
    "sports expert",
]

AI_ROLE_OPTIONS_ZW = [
    "helpful assistant",
    "code assistant",
    "code reviewer",
    "text improver",
    "cinema expert",
    "sports expert",
]

en = Locale(
    ai_role_options=AI_ROLE_OPTIONS_EN,
    ai_role_prefix="You are an assistant",
    ai_role_postfix="Answer as concisely as possible.",
    title="Gemini AI Echo Chamber (Test)",
    choose_language="Choose UI Language",
    language="English",
    lang_code='en',
    chat_placeholder="Your Question:",
    chat_messages="Messages:",
    chat_run_btn="✔️ Send",
    chat_clear_btn="New Topic",
    clear_doc_btn=":x: Clear Doc",
    enable_search_label="Enable Web Search",
    chat_save_btn="Save",
    file_upload_label="You can chat with an uploaded file (your file will never be saved anywhere)",
    temperature_label="Model Temperature",
    login_prompt="Login",
    logout_prompt="Logout",
    username_prompt="Username/password is incorrect",
    password_prompt="Please enter your username and password",
    choose_llm_prompt="Choose Your Model",
    support_message="Please report any issues or suggestions to tqye@yahoo.com<br>If you like this App please <a href='https://buymeacoffee.com/tqye2006'>buy me a :coffee:🌝 </a><p> To use other models：<br><a href='https://askcrp.streamlit.app'>Command R+</a><br><a href='https://gptecho.streamlit.app'>OpenAI GPT-4o</a><br><a href='https://claudeecho.streamlit.app'>Claude</a><br><p>Other Tools：<br><a href='https://imagicapp.streamlit.app'>Image Magic</a>",
    select_placeholder2="Select Role",
    stt_placeholder="Play Audio",
    radio_placeholder="UI Language",
    radio_text1="English",
    radio_text2="中文",
)

zw = Locale(
    ai_role_options=AI_ROLE_OPTIONS_ZW,
    ai_role_prefix="You are an assistant",
    ai_role_postfix="Answer as concisely as possible.",
    title="Gemini AI 回音室（测试版）",
    choose_language="选择界面语言",
    language="中文·",
    lang_code='zh-CN',
    chat_placeholder="请输入你的问题或提示:",
    chat_messages="聊天内容:",
    chat_run_btn="✔️ 提交",
    chat_clear_btn=":new: 新话题",
    clear_doc_btn=":x: 清空文件",
    enable_search_label="启用网络搜索",
    chat_save_btn="保存",
    file_upload_label="你可以询问一个上传的文件或图片（文件内容只在内存，不会被保留）",
    temperature_label="模型温度",
    login_prompt="登陆",
    logout_prompt="退出",
    username_prompt="用户名/密码错误",
    password_prompt="请输入用户名和密码",
    choose_llm_prompt="请选择你想使用的AI模型",
    support_message="如遇什么问题或有什么建议，反馈，请电 tqye@yahoo.com<br><br>使用其它模型<br><a href='https://askcrp.streamlit.app'>Command R+</a><br><a href='https://gptecho.streamlit.app'>OpenAI GPT-4o</a><br><a href='https://claudeecho.streamlit.app'>Claude</a><br><br>其它小工具：<br><a href='https://imagicapp.streamlit.app'>照片增强，去背景等</a>",
    select_placeholder2="选择AI的角色",
    stt_placeholder="播放",
    radio_placeholder="选择界面语言",
    radio_text1="English",
    radio_text2="中文",
)

st.set_page_config(page_title="Echo Gemini AI", 
                   initial_sidebar_state="expanded", 
                   menu_items={
                    'Report a bug': "mailto:tqye2006@gmail.com",
                    'About': "# For Experiment Only. Nov-2023"}
    )


sendmail = True

current_user = "**new_chat**"
BASE_PROMPT = "You are a helpful assistant who can answer or handle all my queries!"

# system messages and/or context
set_context_all = {"不预设（通用）": ""}
set_context_all.update(libs.set_sys_context)

def get_remote_ip() -> str:
    """Get remote ip."""

    try:
        ctx = get_script_run_ctx()
        if ctx is None:
            return None

        session_info = runtime.get_instance().get_client(ctx.session_id)
        if session_info is None:
            return None
    except Exception as e:
        return None

    return session_info.request.remote_ip


def get_client_ip():
    '''
    workaround solution, via 'https://api.ipify.org?format=json' for get client ip
    example:
    ip_address = client_ip()  # now you have it in the host...
    st.write(ip_address)  # so you can log it, etc.    
    '''
    url = 'https://api.ipify.org?format=json'

    script = (f'await fetch("{url}").then('
                'function(response) {'
                    'return response.json();'
                '})')

    ip_address = ""
    try:
        result = st_javascript(script)
        if isinstance(result, dict) and 'ip' in result:
            ip_address = result['ip']
        else:
            ip_address = "unknown_ip"
    except:
        pass
        
    return ip_address

@st.cache_data()
def get_geolocation(ip_address):
    #reader = geolite2.reader()
    #location = reader.get(ip_address)
    #geolite2.close()

    url =f'https://ipapi.co/{ip_address}/json/'

    try:
        # Make the GET requests
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        location = {
            "city" : data.get("city)"),
            "region" : data.get("region"),
            "country" : data.get("country_name"),
            }
        return location
    except requests.RequestException as ex:
        print(f"An error: {ex}")
        return None


def randomword(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))
        
def role_change_callback(arg):
    try:
        st.session_state[arg + current_user + "value"] = st.session_state[arg + current_user]

        sys_msg = ""
        for ctx in [
            set_context_all[st.session_state["context_select" + current_user]],
            st.session_state["context_input" + current_user],
        ]:
            if ctx != "":
                sys_msg += ctx + '\n'
    except Exception as ex:
        sys_msg = ""


    if len(sys_msg.strip()) > 10:
        st.session_state.sys_prompt = sys_msg
    else:
        st.session_state.sys_prompt = BASE_PROMPT


@st.cache_data()
def get_app_folder():
    app_folder = os.path.dirname(__file__)

    return app_folder

def save_log(query, res, total_tokens):
    '''
    Log an event or error
    '''
    now = datetime.now() # current date and time
    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
    remote_ip = get_client_ip()
    app_folder = get_app_folder()
    try:
        f = open(app_folder + "/gptGate.log", "a", encoding='utf-8',)
        f.write(f'[{date_time}] {st.session_state.user}:({remote_ip}):\n')
        f.write(f'[You]: {query}\n')
        f.write(f'[GPT]: {res}\n')
        f.write(f'[Tokens]: {total_tokens}\n')
        f.write(f"User ip: {st.session_state.user_ip}")
        f.write(f"User Geo: {st.session_state.user_location}")
        f.write(100 * '-' + '\n\n')
        f.close()
    except Exception as ex:
        print(f"Exception: {ex}")
        pass
        
    print(f'[{date_time}]: {st.session_state.user}: {remote_ip}\n')
    print(res+'\n')

#@st.cache_data(show_spinner=False)
def send_mail(query, res, total_tokens):
    '''
    '''
    now = datetime.now() # current date and time
    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
    message = f'[{date_time}] {st.session_state.user}:({st.session_state.user_ip}:: {st.session_state.user_location}):\n'
    message += f'Model: {st.session_state.model_version}\n'
    message += f'[You]: {query}\n'
    if 'text' in res:
        generated_text = res["text"]
    else:
        generated_text = "No text generated!"

    message += f'[Gemini]: {generated_text}\n'
    message += f'[Tokens]: {total_tokens}\n'

    # Set up the SMTP server and log into your account
    smtp_server = "smtp.gmail.com"
    port = 587
    # sender_email = "your_email@gmail.com"
    # password = "your_password"
    sender_email = st.secrets["gmail_user"]
    password = st.secrets["gmail_passwd"]

    server = smtplib.SMTP(smtp_server, port)
    server.starttls()
    server.login(sender_email, password)

    # Create the MIMEMultipart message object and load it with appropriate headers for From, To, and Subject fields
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = st.secrets["receive_mail"]
    msg['Subject'] = f"Chat from {st.session_state.user}"

    # Add your message body
    body = message
    msg.attach(MIMEText(body, 'plain'))

    try:
        if "image" in res:
            print("Attaching Image found!")
            # Open the image file in binary mode
            with BytesIO() as buffer:
                imageFile = res["image"]
                imageFile.save(buffer, format="JPEG")
                img = MIMEImage(buffer.getbuffer())       
                # Attach the image to the MIMEMultipart object
                msg.attach(img)
    except Exception as e:
        print(f"Error: {str(e)}", 0)

    # Send the message using the SMTP server object
    server.send_message(msg)
    server.quit()

def Display_Uploaded_Image(img_str:str):
    buffer = BytesIO()
    img_data = b64decode(img_str)
    img = Image.open(BytesIO(img_data))
    img.thumbnail((300,300), Image.Resampling.LANCZOS)
    st.write(img)

def Show_Audio_Player(ai_content: str) -> None:
    sound_file = BytesIO()
    try:
        lang = detect(ai_content)
        print("Language:", lang)
        if lang in ['zh', 'zh-CN', 'en', 'de', 'fr'] :
            tts = gTTS(text=ai_content, lang=lang)
            #if st.session_state['locale'] is zw:
            #    tts = gTTS(text=ai_content, lang='zh')
            #else:
            #    tts = gTTS(text=ai_content, lang='en')
            tts.write_to_fp(sound_file)
            st.session_state.gtts_placeholder.write(st.session_state.locale.stt_placeholder)
            st.session_state.gtts_placeholder.audio(sound_file)
    except gTTSError as err:
        #st.session_state.gtts_placeholder.error(err)
        save_log("Error", str(err), 0)
    except Exception as ex:
        #st.session_state.gtts_placeholder.error(err)
        save_log("Error", str(ex), 0)

def Login() -> str:
    with open('./config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    random_key = randomword(10)
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
    
    fields = {'Form name':st.session_state.locale.login_prompt[0], 'Username':'Username', 'Password':'Password', 'Login':st.session_state.locale.login_prompt[0], 'Captcha':'Captcha'}
    
    try:
        authenticator.login(location='main', fields=fields)
        # authenticator.experimental_guest_login('Login with Google',
        #                                     provider='google',
        #                                     oauth2=config['oauth2'])
        # authenticator.experimental_guest_login('Login with Microsoft',
        #                                     provider='microsoft',
        #                                     oauth2=config['oauth2'])

        # Authenticating user
        if st.session_state['authentication_status']:
            authenticator.logout()
            st.write(f'Welcome *{st.session_state["name"]}*')
            #st.title('Some content')
        elif st.session_state['authentication_status'] is False:
            #st.error('Username/password is incorrect')
            st.error(st.session_state.locale.username_prompt[0])
            st.warning("如果您想使用该服务，请联系管理员（tqye@yahoo.com)申请一个账号！")
        elif st.session_state['authentication_status'] is None:
            #st.warning('Please enter your username and password')
            st.warning(st.session_state.locale.password_prompt[0])
            st.warning("如果您想使用该服务，请联系管理员（tqye@yahoo.com)申请一个账号！")                                                                                                                 
        else:
            st.warning(st.session_state.locale.password_prompt[0])
            st.warning("如果您想使用该服务，请联系管理员（tqye@yahoo.com)申请一个账号！")    
    except Exception as e:
        st.error(e)

    #return name, authentication_status, username
    return st.session_state["name"], st.session_state['authentication_status'], st.session_state['username']


def Clear_Chat() -> None:
    st.session_state.history = []
    st.session_state.messages = []
    st.session_state.contents = []
    st.session_state.user_text = ""
    st.session_state.loaded_content = ""
    st.session_state.loaded_image = None
    #st.session_state.locale = zw

    st.session_state.key += "1"     # HACK use the following two lines to reset update the file_uploader key
    st.rerun()


def Delete_Files() -> None:

    st.session_state.loaded_content = ""
    st.session_state.loaded_image = None
    st.session_state.contents = []
    st.session_state.key = str(random.randint(1000, 10000000))      # HACK use the following two lines to reset update the file_uploader key
    st.rerun()

def Model_Changed() -> None:
    if "2.0 flash Exp" in st.session_state.model_version:
        st.session_state.enable_search = False
        st.session_state.search_disabled = True
    else:
        st.session_state.search_disabled = False

    Delete_Files()
    
def Show_Images(desc, images):
    for image in images:
        st.image(image, caption=desc)

def Show_Messages(placeholder):

    #print(f"Number of messages: {len(st.session_state.messages)}")
    #with placeholder:
    for message in st.session_state.messages[::-1]: # reverse order
    #for message in st.session_state.messages[1:]:
        #print(f"Show Message: {message}")
        if message['role'] == 'user':
            role = 'You'
            alignment = "right"
        elif message['role'] == 'model':
            role = 'AI'
            alignment = "left"
        else:
            role = message['role']
            alignment = "left"

        st.markdown(f"<div style='text-align: {alignment};'><b>{role}</b>:</div>", unsafe_allow_html=True)

        #print(f"Show Message Parts: {message['parts']}")

        if isinstance(message['parts'], list):
            if "text" in message['parts'][0]:
                text = message['parts'][0]['text']
            else:
                text = f"{message['parts'][0]}"
            #with st.align(alignment):
            #    st.write(text, unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: {alignment};'>{text}</div>", unsafe_allow_html=True)
        elif isinstance(message['parts'], dict):
            if "text" in message['parts']:
                text = message['parts']['text']
                #with st.align(alignment):
                #    st.write(text, unsafe_allow_html=True)
                st.markdown(f"<div style='text-align: {alignment};'>{text}</div>", unsafe_allow_html=True)
            if "image" in message['parts']:
                st.image(message['parts']["image"])
        else:
            text = f"{message['parts']}"
            #with st.align(alignment):
                #st.write(text, unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: {alignment};'>{text}</div>", unsafe_allow_html=True)


def Imagen_Creation(prompt, npics):
    '''
    '''
    isOK = False
    generated_images = []

    #-- Using imagen-3.0-generate-002 Model ------
    try:
        response = st.session_state.client.models.generate_images(
            model='imagen-3.0-generate-002',
            contents = prompt,
            config=genai.types.GenerateImagesConfig(number_of_images= npics,
                                              output_mime_type="image/jpeg",
                                              safety_filter_level= "BLOCK_ONLY_HIGH",
                                              person_generation = "ALLOW_ADULT",
                                                )
            ) 

        for generated_image in response.generated_images:
            image = Image.open(BytesIO(generated_image.image.image_bytes))
            st.image(image)
            generated_images.append(image)
            isOK = True
    except Exception as e:
        print(f"Imagen-3.0 model returned error! str({e})")

    return isOK, generated_images    

def Model_Completion(contents: list, sys_prompt: str = BASE_PROMPT, temperature: float = 0.7):
    '''
    '''    
    #print("DEBUG incoming contents:", contents)

    if(len(contents) > MAX_MESSAGES+1):
        contents.pop(1)
        contents.pop(1)

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    tokens = 0
    ret_content = {}
    try:
        if "2.0 flash Exp" in st.session_state.model_version:
            response = st.session_state.client.models.generate_content(
                model = "models/gemini-2.0-flash-exp",
                contents = contents,
                config=genai.types.GenerateContentConfig(response_modalities=['Text', 'Image'],
                                                         safety_settings=safety_settings,
                                                         )
                )

            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    print(part.text)
                    ret_content["text"] = part.text
                    #st.write(part.text)
                    st.session_state["contents"].append(part.text)
                elif part.inline_data is not None:
                    image = Image.open(BytesIO(part.inline_data.data))
                    #image.show()
                    ret_content["image"] = image
                    st.session_state["contents"].append(image)
                    #st.image(image)
        else:
            if st.session_state.enable_search:
                response = st.session_state.client.models.generate_content(
                    model = st.session_state.llm,
                    contents = contents,
                    config=genai.types.GenerateContentConfig(response_modalities=['Text'],
                                                            system_instruction=sys_prompt,
                                                            temperature=temperature,
                                                            tools=[
                                                                types.Tool(google_search=types.GoogleSearch())
                                                            ],
                                                            )
                    )
            else:
                response = st.session_state.client.models.generate_content(
                    model = st.session_state.llm,
                    contents = contents,
                    config=genai.types.GenerateContentConfig(response_modalities=['Text'],
                                                            system_instruction=sys_prompt,
                                                            temperature=temperature,
                                                            )
                    )
                            
            # If the AI role is '汉语新解' or '诗词卡片', remove the code marks
            if st.session_state["context_select" + current_user + "value"] in ['汉语新解', '诗词卡片']:
                ret_content = libs.remove_contexts(response.text)
            else:
                ret_content["text"] = response.text

        print(f"AI model returned: {ret_content}")
        print(response.usage_metadata)
        # ( prompt_token_count: 11, candidates_token_count: 73, total_token_count: 84 )
        tokens = response.usage_metadata.total_token_count
    except Exception as e:
        ret_content["text"] = f"AI model returned error! str({e})"

    # construct chat histrory

    return ret_content, tokens

#@st.cache_data()
def Create_Client():
    '''
    '''
    client = genai.Client(api_key=st.secrets["api_key"])

    return client

@st.cache_resource()
def Main_Title(text: str) -> None:
    st.markdown(f'<h1 style="background-color:#ffffff;color:#049ca4;font-weight:bold;font-size:22px;border-radius:2%;">{text}</h1>', unsafe_allow_html=True)

##############################################
################ MAIN ########################
##############################################
def main(argv):

    ## ----- Start --------
    #st.header(st.session_state.locale.title[0])
    Main_Title(st.session_state.locale.title[0])
    st.markdown(f"Hello {st.session_state.user}", unsafe_allow_html=True)
    try:
        st.session_state.user_ip = get_client_ip()
        st.session_state.user_location = get_geolocation(st.session_state.user_ip)
    except Exception as ex:
        st.session_state.user_ip = "unknown_ip"
        st.session_state.user_location = "unknown_location"
        print(f"Exception getting user ip/location: {ex}")

    st.session_state.client = Create_Client()
    
    st.session_state.model_version = st.selectbox(label=st.session_state.locale.choose_llm_prompt[0], 
                                                  options=("Gemini 3.0 Pro (最强大脑)",
                                                           "Gemini 2.0 flash Exp （图，文）", 
                                                           "Gemini 2.5 Pro", 
                                                           "Gemini 2.5 flash",), on_change=Model_Changed)
    if "2.0 flash Exp" in st.session_state.model_version:
        st.session_state.llm = "gemini-2.0-flash"
        st.session_state.enable_search = False
        st.session_state.search_disabled = True
    elif "3.0 Pro" in st.session_state.model_version:
        st.session_state.llm = "gemini-3-pro-preview"
        st.session_state.search_disabled = False
    elif "2.5 Pro" in st.session_state.model_version:
        st.session_state.llm = "ggemini-2.5-pro"
        st.session_state.search_disabled = False
    elif st.session_state.model_version == "Gemini 2.5 flash":
        st.session_state.llm = "gemini-2.5-flash"
        st.session_state.search_disabled = False
    else:
        st.session_state.llm = "gemini-2.5-pro"
        st.session_state.search_disabled = False

    st.sidebar.button(st.session_state.locale.chat_clear_btn[0], on_click=Clear_Chat)
    st.session_state.temperature = st.sidebar.slider(label=st.session_state.locale.temperature_label[0], min_value=0.1, max_value=2.0, value=0.7, step=0.05)
    st.sidebar.markdown("<p class='tiny-font'>注意：若接下来的话题与之前的不相关，请点击“新话题”按钮，以确保新话题不会受之前内容的影响，同时也有助于节省字符传输量。谢谢！</p>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<p class='tiny-font'>{st.session_state.locale.support_message[0]}", unsafe_allow_html=True)

    sys_role_placeholder = st.write("AI的角色: **" + st.session_state["context_select" + current_user + "value"] + "**")
    tab_input, tab_context = st.tabs(
        ["💬 聊天", "🤖 AI角色预设"]
    )

    with tab_context:
        set_context_list = list(set_context_all.keys())
        #print(f"set_context_list: {set_context_list}")
        #print(st.session_state["context_select" + current_user + "value"])
        context_select_index = set_context_list.index(
            st.session_state["context_select" + current_user + "value"]
        )
        st.selectbox(
            label="选择角色预设",
            options=set_context_list,
            key="context_select" + current_user,
            index=context_select_index,
            on_change=role_change_callback,
            args=("context_select",),
        )
        st.caption(set_context_all[st.session_state["context_select" + current_user]])

        st.text_area(
            label="补充或自定义上下文：",
            key="context_input" + current_user,
            value=st.session_state["context_input" + current_user + "value"],
            on_change=role_change_callback,
            args=("context_input",),
        )

    with tab_input:
        st.session_state.chats_placeholder = st.empty()
        st.session_state.gtts_placeholder = st.empty()
        st.session_state.uploading_file_placeholder = st.empty()
        st.session_state.uploaded_filename_placeholder = st.empty()
        st.session_state.buttons_placeholder = st.empty()
        st.session_state.input_placeholder = st.empty()

        # #with chats_placeholder:
        # Show_Messages(chats_placeholder)

        pil_image = None

        with st.session_state.uploading_file_placeholder:
            uploaded_file = st.file_uploader(label=st.session_state.locale.file_upload_label[0], type=['docx', 'txt', 'pdf', 'csv', 'jpg','jpeg', 'png', 'webp'], key=st.session_state.key, accept_multiple_files=False,)
            if uploaded_file is not None:
                mime_type = uploaded_file.type
                if uploaded_file.name.split(".")[-1] in ['jpeg', 'jpg', 'png', 'webp']:
                        pil_image = Image.open(uploaded_file)
                        st.session_state.loaded_image, ierror = libs.GetContexts(uploaded_file)
                        if ierror != 0:
                            st.session_state.uploaded_filename_placeholder.warning(st.session_state.loaded_content)
                        else:
                            with st.session_state.uploaded_filename_placeholder:
                                Display_Uploaded_Image(st.session_state.loaded_image)
                else:
                    st.session_state.loaded_content, ierror = libs.GetContexts(uploaded_file)
                    if ierror != 0:
                        st.session_state.uploaded_filename_placeholder.warning(st.session_state.loaded_content)
                    else:
                        doc_len = len(st.session_state.loaded_content)
                        #print(f"The size of the document:  {len(st.session_state.loaded_content)}")
                        st.session_state.uploaded_filename_placeholder.write(f"{uploaded_file.name} ({doc_len})")
                        st.session_state.enable_search = False
                        st.session_state.search_disabled = True
        with st.session_state.buttons_placeholder:
            c1, c2 = st.columns(2)
            with c1:
                st.session_state.new_topic_button = st.button(label=st.session_state.locale.chat_clear_btn[0], key="newTopic", on_click=Clear_Chat)
            with c2:
                st.session_state.enable_search = st.checkbox(label=st.session_state.locale.enable_search_label[0], disabled=st.session_state.search_disabled, value=st.session_state.enable_search)

        user_input = st.session_state.input_placeholder.text_area(label=st.session_state.locale.chat_placeholder[0], value=st.session_state.user_text, max_chars=8000, key="1")
        send_button = st.button(st.session_state.locale.chat_run_btn[0], disabled=st.session_state.out_quota)
        if send_button :
            parts = []
            print(f"{st.session_state.user}: {user_input}")
            if(user_input.strip() != ''):
                prompt = user_input.strip()
                prefixes = ["!!!", "！！！"]
                if(prompt.startswith(tuple(prefixes))):
                    if (TEXT2IMG_ENABLES == "yes"): 
                        #-- Using imagen-3.0-generate-002 Model ------
                        prompt = " ".join(prompt.split()[1:])
                        print(f"DEBUG: {prompt}")
                        with st.spinner('Wait ...'):
                            isOK, ret_images = Imagen_Creation(prompt, 2)
                            if(isOK == True):
                                st.session_state.total_tokens += 1500
                                save_log(prompt, "image generated", st.session_state.total_tokens)
                                Show_Images(prompt, ret_images)
                            else:
                                save_log(prompt, "画画失败。请等下再试！", st.session_state.total_tokens)
                                st.markdown(f"画画失败。请等下再试！", unsafe_allow_html=True)
                    else:
                        st.markdown(f"画画暂时没有开放，请以后再试！", unsafe_allow_html=True)
                        save_log(prompt, "画画暂时没有开放，请以后再试！", st.session_state.total_tokens)
                else:
                    print(f"I am using the model: {st.session_state.model_version}")
                    parts.append(prompt)
                    # if st.session_state.model_version == "Gemini 2.0 flash Exp":
                    #     parts.append(prompt)
                    # else: 
                    #     parts.append({"text": prompt})
                    if st.session_state.loaded_content.strip() != "":
                        print("Context supplied!")
                        parts.append(st.session_state.loaded_content.strip())
                    if st.session_state.loaded_image != None:
                        print("Image supplied!")
                        parts.append(pil_image)

                    st.session_state.messages += [{"role": "user", "parts": parts}]
                    #print(f"DEBUG0: {st.session_state.messages}\n")

                    with st.spinner('Wait ...'):
                        if "2.0 flash Exp" in st.session_state.model_version:
                            st.session_state.contents += parts
                            #answer, tokens = Model_Completion(parts)
                            answer, tokens = Model_Completion(st.session_state.contents)
                        else:
                            st.session_state.contents += parts
                            answer, tokens = Model_Completion(st.session_state.contents, st.session_state.sys_prompt, st.session_state.temperature)
                        st.session_state.total_queries += 1
                        st.session_state.total_tokens += tokens

                        #print(f"RETURNED ANSWER: {answer}\n")

                        if 'text' in answer:
                            generated_text = answer["text"]
                            Show_Audio_Player(generated_text)
                        else:
                            generated_text = "No text generated!"

                        if "2.0 flash Exp" in st.session_state.model_version:
                            st.session_state["messages"] += [{"role": "model", "parts": answer}]
                        else:
                            st.session_state["messages"] += [{"role": "model", "parts": [answer]}]

                    #print(f"DEBUG2: {st.session_state.messages}")

                    #with chats_placeholder:
                    Show_Messages(st.session_state.chats_placeholder)

                    save_log(prompt, generated_text, st.session_state.total_tokens)
                    if sendmail:
                        send_mail(prompt, answer, st.session_state.total_tokens)

        #cost = 8*0.015 * st.session_state.total_tokens /1000
        #if st.session_state.user_id in ["wenli2000", "yezheng", "yayuan181"]:
        #    small_print = f"你目前用掉 {st.session_state.total_tokens} 字符"
        #else:
        #    #small_print = f"你目前用掉 {st.session_state.total_tokens} 字符 (约人民币{cost:.4f}元)"
        #    small_print = f"你目前用掉 {st.session_state.total_tokens} 字符"
        small_print = f"你目前用掉 {st.session_state.total_tokens} 字符"
        st.markdown("""
            <style>
            .tiny-font {font-size:11px !important;}
            </style>
            """, unsafe_allow_html=True)
        st.markdown(f'<p class="tiny-font">{small_print}</p>', unsafe_allow_html=True)

        if st.session_state.user not in VALID_USERS and st.session_state.total_queries > TOTAL_TRIALS:
            st.session_state.out_quota = True
            st.warning("# 你已经超过了今天的试用额度。请稍后再试！或联系管理员 tqye@yahoo.com 申请一个账号。")

##############################
if __name__ == "__main__":

    # Initiaiise session_state elements
    if "user" not in st.session_state:
        st.session_state.user = ""

    if "locale" not in st.session_state:
        st.session_state['locale'] = zw

    if "user_text" not in st.session_state:
        st.session_state.user_text = ""

    if "user_ip" not in st.session_state:
        st.session_state.user_ip = get_client_ip()

    if "user_id" not in st.session_state:
        try:
            st.session_state.user_id = get_geolocation(st.session_state.user_ip)["city"]
        except:
            st.session_state.user_id = get_geolocation(st.session_state.user_ip)

    if "user_loacation" not in st.session_state:
        st.session_state.user_location = None

    if "locale" not in st.session_state:
        st.session_state['locale'] = zw

    if "model_version" not in st.session_state:
        st.session_state.model_version = "Gemini 2.0 flash"

    if "temperature" not in st.session_state:
        st.session_state.temperature = 0.7

    if "loaded_content" not in st.session_state:
        st.session_state.loaded_content = ""

    if "loaded_image" not in st.session_state:
        st.session_state.loaded_image = None

    if "user_text" not in st.session_state:
        st.session_state.user_text = ""

    if "history" not in st.session_state:
        st.session_state.history = [
                {"role": "user", "parts": "Hello"},
                {"role": "model", "parts": "Great to meet you. How can I assist you?"},
            ]

    if "enable_search" not in st.session_state:
        st.session_state.enable_search = False

    if "search_disabled" not in st.session_state:
        st.session_state.search_disabled = False

    if 'total_tokens' not in st.session_state:
        st.session_state.total_tokens = 0

    if 'tokens' not in st.session_state:
        st.session_state["tokens"] = 0

    if 'key' not in st.session_state:
        st.session_state.key = str(random.randint(1000, 10000000))    

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # used by 2.0 flash exp model
    if "contents" not in st.session_state:
        st.session_state.contents = []

    if "sys_prompt" not in st.session_state:
        st.session_state.sys_prompt = BASE_PROMPT

    if 'total_queries' not in st.session_state:
        st.session_state.total_queries = 0

    if 'out_quota' not in st.session_state:
        st.session_state.out_quota = False

    #if (txt2img_enabled == True):
    #    pipe = get_sd_model_pipe(model_id)
    
    st.markdown(
            """
                <style>
                    .appview-container .block-container {{
                        padding-top: {padding_top}rem;
                        padding-bottom: {padding_bottom}rem;
                    }}
                    .sidebar .sidebar-content {{
                        width: 160px;
                    }}
                    .st-emotion-cache-fis6aj {{
                        display: none;
                    }}
                    .st-emotion-cache-9ycgxx {{
                        display: none;
                    }}
                </style>""".format(padding_top=1, padding_bottom=10),
            unsafe_allow_html=True,
    )

    ##---------- Disable Login For Now ------------
    # st.session_state.user, st.session_state.authentication_status, st.session_state.user_id = Login()
    # if st.session_state.user != None and st.session_state.user != "" and st.session_state.user != "invalid":
    #     current_user = st.session_state.user_id

    #     if "context_select" + current_user + "value" not in st.session_state:
    #         st.session_state["context_select" + current_user + "value"] = '不预设（通用）'

    #     if "context_input" + current_user + "value" not in st.session_state:
    #         st.session_state["context_input" + current_user + "value"] = ""

    #     main(sys.argv)
    #----------------------------------------------

    # Create a input box for inviting user to enter their given name
    if st.session_state.user == "" or st.session_state.user is None:
        st.write("欢迎来到Gemini AI 回音室！")
        st.session_state.user = st.text_input(label="请输入你的ID：", value="", max_chars=20)
        if st.session_state.user != None and st.session_state.user != "" and st.session_state.user != "invalid":
            current_user = st.session_state.user
            if "context_select" + current_user + "value" not in st.session_state:
                st.session_state["context_select" + current_user + "value"] = '不预设（通用）'
            if "context_input" + current_user + "value" not in st.session_state:
                st.session_state["context_input" + current_user + "value"] = ""

            main(sys.argv)
    else:
        current_user = st.session_state.user
        if "context_select" + current_user + "value" not in st.session_state:
            st.session_state["context_select" + current_user + "value"] = '不预设（通用）'
        if "context_input" + current_user + "value" not in st.session_state:
            st.session_state["context_input" + current_user + "value"] = ""

        main(sys.argv)


    
