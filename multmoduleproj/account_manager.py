import wx
import pandas as pd
from pathlib import Path
import random
import string
from twilio.rest import Client
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_VERIFY_SERVICE_ID

class TwoFactorDialog(wx.Dialog):
    def __init__(self, parent, phone_number):
        super().__init__(parent, title="Two Factor Authentication", size=(300, 200))
        self.phone_number = phone_number
        self.result = False
        self.init_ui()
        self.send_verification_code()
        
    def init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        info_text = wx.StaticText(panel, label=f"A verification code has been sent to\n{self.phone_number}")
        self.code_input = wx.TextCtrl(panel)
        verify_btn = wx.Button(panel, label='Verify')
        
        vbox.Add(info_text, flag=wx.ALL|wx.CENTER, border=5)
        vbox.Add(wx.StaticText(panel, label='Enter verification code:'), flag=wx.ALL, border=5)
        vbox.Add(self.code_input, flag=wx.EXPAND|wx.ALL, border=5)
        vbox.Add(verify_btn, flag=wx.ALL|wx.CENTER, border=5)
        
        verify_btn.Bind(wx.EVT_BUTTON, self.on_verify)
        panel.SetSizer(vbox)
        
    def send_verification_code(self):
        try:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            verification = client.verify \
                .v2 \
                .services(TWILIO_VERIFY_SERVICE_ID) \
                .verifications \
                .create(to=self.phone_number, channel='sms')
            return True
        except Exception as e:
            wx.MessageBox(f'Failed to send verification code: {str(e)}', 'Error')
            self.Close()
            return False
        
    def verify_code(self, code):
        try:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            check = client.verify \
                .v2 \
                .services(TWILIO_VERIFY_SERVICE_ID) \
                .verification_checks \
                .create(to=self.phone_number, code=code)
            return check.status == 'approved'
        except Exception:
            return False
        
    def on_verify(self, event):
        code = self.code_input.GetValue()
        if self.verify_code(code):
            self.result = True
            self.Close()
        else:
            wx.MessageBox('Invalid verification code', 'Error')

class HomePage(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent=parent, title='Home Page')
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        sign_out_item = file_menu.Append(wx.ID_ANY, 'Sign Out')
        menubar.Append(file_menu, 'Menu')
        self.SetMenuBar(menubar)
        
        welcome = wx.StaticText(panel, label='Good Job! You Logged In!')
        font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        welcome.SetFont(font)
        
        vbox.Add(welcome, flag=wx.ALL|wx.CENTER, border=20)
        panel.SetSizer(vbox)
        
        self.Bind(wx.EVT_MENU, self.on_sign_out, sign_out_item)
        self.Bind(wx.EVT_CLOSE, self.on_sign_out)
        
        self.SetSize(400, 300)
        self.Center()
        
    def on_sign_out(self, event):
        self.Hide()
        self.parent.Show()
        self.Destroy()

class LoginFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='Account Manager')
        self.data_file = 'users.csv'
        self.init_ui()
        
    def init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        self.username = wx.TextCtrl(panel)
        self.password = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
        self.phone = wx.TextCtrl(panel)
        login_btn = wx.Button(panel, label='Login')
        register_btn = wx.Button(panel, label='Register')
        
        vbox.Add(wx.StaticText(panel, label='Username:'), flag=wx.ALL, border=5)
        vbox.Add(self.username, flag=wx.EXPAND|wx.ALL, border=5)
        vbox.Add(wx.StaticText(panel, label='Password:'), flag=wx.ALL, border=5)
        vbox.Add(self.password, flag=wx.EXPAND|wx.ALL, border=5)
        vbox.Add(wx.StaticText(panel, label='Phone Number (+1XXXXXXXXXX):'), flag=wx.ALL, border=5)
        vbox.Add(self.phone, flag=wx.EXPAND|wx.ALL, border=5)
        vbox.Add(login_btn, flag=wx.ALL|wx.CENTER, border=5)
        vbox.Add(register_btn, flag=wx.ALL|wx.CENTER, border=5)
        
        login_btn.Bind(wx.EVT_BUTTON, self.on_login)
        register_btn.Bind(wx.EVT_BUTTON, self.on_register)
        
        panel.SetSizer(vbox)
        self.SetSize(300, 350)
        self.Center()
        
    def load_users(self):
        if Path(self.data_file).exists():
            return pd.read_csv(self.data_file)
        return pd.DataFrame(columns=['username', 'password', 'phone'])
    
    def save_users(self, df):
        df.to_csv(self.data_file, index=False)
        
    def on_login(self, event):
        username = self.username.GetValue()
        password = self.password.GetValue()
        phone = self.phone.GetValue()
        
        users = self.load_users()
        user = users[users['username'] == username]
        
        if not user.empty and user.iloc[0]['password'] == password:
            dialog = TwoFactorDialog(self, phone)
            dialog.ShowModal()
            
            if dialog.result:
                self.Hide()
                home = HomePage(self)
                home.Show()
            dialog.Destroy()
        else:
            wx.MessageBox('Invalid username or password', 'Error')
            
    def on_register(self, event):
        username = self.username.GetValue()
        password = self.password.GetValue()
        phone = self.phone.GetValue()
        
        if not username or not password or not phone:
            wx.MessageBox('Please fill in all fields', 'Error')
            return
            
        users = self.load_users()
        if username in users['username'].values:
            wx.MessageBox('Username already exists', 'Error')
            return
            
        new_user = pd.DataFrame([[username, password, phone]], 
                               columns=['username', 'password', 'phone'])
        users = pd.concat([users, new_user], ignore_index=True)
        self.save_users(users)
        wx.MessageBox('Registration successful!', 'Success')

if __name__ == '__main__':
    app = wx.App()
    frame = LoginFrame()
    frame.Show()
    app.MainLoop()