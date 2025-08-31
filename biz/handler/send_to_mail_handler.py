import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

class EmailSender:
    """邮件发送器类"""
    
    # 常见邮箱的SMTP配置
    SMTP_CONFIGS = {
        'qq': {
            'server': 'smtp.qq.com',
            'port': 465,
            'ssl': True
        },
        '163': {
            'server': 'smtp.163.com',
            'port': 465,
            'ssl': True
        },
        'gmail': {
            'server': 'smtp.gmail.com',
            'port': 587,
            'ssl': False
        },
        'outlook': {
            'server': 'smtp.office365.com',
            'port': 587,
            'ssl': False
        }
    }
    
    def __init__(self, email_type, username, password):
        """
        初始化邮件发送器
        
        Args:
            email_type: 邮箱类型 ('qq', '163', 'gmail', 'outlook')
            username: 邮箱用户名
            password: 邮箱密码/授权码
        """
        config = self.SMTP_CONFIGS.get(email_type.lower())
        if not config:
            raise ValueError(f"不支持的邮箱类型: {email_type}")
        
        self.smtp_server = config['server']
        self.smtp_port = config['port']
        self.use_ssl = config['ssl']
        self.username = username
        self.password = password
    
    def send_email(self, from_addr, to_addrs, subject, body, 
                  attachments=None, is_html=False):
        """
        发送邮件
        
        Args:
            attachments: 附件路径列表
            is_html: 是否为HTML格式
        """
        # 创建邮件对象
        if attachments or is_html:
            msg = MIMEMultipart()
        else:
            msg = MIMEMultipart()
        
        msg['From'] = from_addr
        msg['To'] = ', '.join(to_addrs) if isinstance(to_addrs, list) else to_addrs
        msg['Subject'] = subject
        
        # 添加正文
        content_type = 'html' if is_html else 'plain'
        msg.attach(MIMEText(body, content_type, 'utf-8'))
        
        # 添加附件
        if attachments:
            for attachment_path in attachments:
                if os.path.exists(attachment_path):
                    filename = os.path.basename(attachment_path)
                    
                    with open(attachment_path, 'rb') as f:
                        attachment = MIMEApplication(f.read())
                    
                    attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                    msg.attach(attachment)
                else:
                    print(f"警告：附件文件不存在: {attachment_path}")
        
        try:
            # 连接服务器
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            
            # 登录并发送
            server.login(self.username, self.password)
            server.sendmail(from_addr, to_addrs, msg.as_string())
            server.quit()
            
            print("邮件发送成功！")
            return True
            
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False

# 使用示例
if __name__ == "__main__":
    # 初始化邮件发送器（QQ邮箱）
    email_sender = EmailSender(
        email_type='163',
        username='finacialreport@163.com',  
        password=''  # 授权码
    )
    
    # 发送带附件的邮件
    email_sender.send_email(
        from_addr='finacialreport@163.com',
        to_addrs=['xyliu0910@163.com'],
        subject='测试邮件',
        body='这是一封测试邮件，包含附件。',
        attachments=['/Users/cheng/Desktop/财报.pdf'],
        is_html=False
    )