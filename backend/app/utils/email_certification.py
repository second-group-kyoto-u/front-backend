import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
import jwt
import secrets
from datetime import datetime, timedelta

# 環境変数から設定を取得
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.example.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', 'user@example.com')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'password')
EMAIL_FROM = os.getenv('EMAIL_FROM', 'noreply@example.com')
BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')
SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')

os.environ['FLASK_ENV'] = 'development'

def send_email(to_email, subject, html_content):
    """メールを送信する関数"""
    # 開発モードでは実際に送信せず、コンソールに出力
    if os.getenv('FLASK_ENV') == 'development':
        print(f"==== メール送信（開発モード） ====")
        print(f"宛先: {to_email}")
        print(f"件名: {subject}")
        print(f"内容:\n{html_content}")
        print(f"================================")
        return True
        
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Date'] = formatdate()
        
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"メール送信エラー: {e}")
        return False

def generate_token(data, expires_in=24):
    """JWT認証トークンを生成する"""
    expiration = datetime.utcnow() + timedelta(hours=expires_in)
    payload = {
        **data,
        'exp': expiration,
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def verify_token(token):
    """トークンを検証する"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def send_password_reset_email(user):
    """パスワードリセット用のメールを送信する"""
    token = generate_token({'user_id': user.id, 'action': 'password_reset'})
    reset_url = f"{BASE_URL}/reset-password/{token}"
    
    subject = "パスワードリセットのご案内"
    html_content = f"""
    <html>
        <body>
            <p>{user.user_name} 様</p>
            <p>パスワードリセットのリクエストを受け付けました。</p>
            <p>以下のリンクをクリックして、パスワードを再設定してください：</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            <p>このリンクは24時間有効です。</p>
            <p>リクエストをしていない場合は、このメールを無視してください。</p>
        </body>
    </html>
    """
    
    return send_email(user.email_address, subject, html_content)

def send_email_verification(user):
    """メール認証用のメールを送信する"""
    token = generate_token({'user_id': user.id, 'action': 'email_verification'})
    verification_url = f"{BASE_URL}/verify-email/{token}"
    
    subject = "メールアドレス認証のご案内"
    html_content = f"""
    <html>
        <body>
            <p>{user.user_name} 様</p>
            <p>アカウント登録ありがとうございます。</p>
            <p>以下のリンクをクリックして、メールアドレスを認証してください：</p>
            <p><a href="{verification_url}">{verification_url}</a></p>
            <p>このリンクは24時間有効です。</p>
        </body>
    </html>
    """
    
    return send_email(user.email_address, subject, html_content) 

# send_email('aaa@a', 'アイウエオかきくけこ', 'bbbbbbbbbb')
# send_email_verification()