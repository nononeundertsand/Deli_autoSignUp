import smtplib
from email.mime.text import MIMEText
from email.header import Header
from typing import cast

def send_email(subject: str, content: str,
               sender_email: str, sender_password: str,
               receiver_email: str,
               smtp_server: str = "smtp.qq.com", smtp_port: int = 587):
    """
    发送邮件

    参数:
        subject: 邮件标题
        content: 邮件内容
        sender_email: 发件人邮箱
        sender_password: 发件人邮箱授权码（不是邮箱密码）
        receiver_email: 收件人邮箱
        smtp_server: SMTP服务器地址，默认为QQ邮箱
        smtp_port: SMTP端口，默认587
    """
    # 构建邮件
    msg = MIMEText(content, "plain", "utf-8")
    msg["From"] = cast(str, Header(sender_email))
    msg["To"] = cast(str, Header(receiver_email))
    msg["Subject"] = cast(str, Header(subject))

    try:
        # 使用SMTP连接服务器并发送邮件
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # 启用TLS加密
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, [receiver_email], msg.as_string())
        server.quit()
        print("邮件发送成功！")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False

# 测试用例
if __name__ == "__main__":
    send_email(
        subject="测试邮件,错误预警!!!",
        content="Hello World, 这是测试邮件。",
        sender_email="",
        sender_password="",
        receiver_email=""
    )