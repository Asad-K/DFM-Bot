import json
import traceback
import sys

from requests import Session
from answer_handler import AnswerHandler
import urllib3

from tkinter import *
import tkinter.messagebox as tkm

import sys


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class IORedirector(object):
    '''A general class for redirecting I/O to this Text widget.'''
    def __init__(self,text_area):
        self.text_area = text_area

class StdoutRedirector(IORedirector):
    '''A class for redirecting stdout to this Text widget.'''
    def write(self,text):
        self.text_area.configure(state='normal')
        self.text_area.insert(END, text)
        self.text_area.configure(state='disabled')
    def flush(self): # needed for file like object
        pass


class InvalidLoginDetails(Exception):
    pass


class UserInterface(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)
        Tk.wm_title(self, "Dr Frost Bot")

        container = Frame(self)

        self.lf = LoginFrame(self, container)
        self.lf.grid(column=0, row=1, padx=10, pady=10)
        self.mf = MainFrame(self, container)
        self.mf.grid(column=0, row=2, padx=10, pady=10)

        self.of = OutputFrame(self, container)
        self.of.grid(column=0, row=3, padx=10, pady=10)

        self.disable(self.mf.winfo_children())

        self.interface = Interface()

    def enable(self, childList):
        for child in childList:
            try:
                child.configure(state='normal')
            except:
                pass
    def disable(self, childList):
        for child in childList:
            try:
                child.configure(state='disable')
            except:
                grandchildList = child.winfo_children()
                for grandchild in grandchildList:
                    grandchild.configure(state='disable')




class LoginFrame(LabelFrame):
    def __init__(self, master, cont):
        super().__init__(master)

        self.master = master

        self.label_username = Label(self, text="Email")
        self.label_password = Label(self, text="Password")

        self.entry_username = Entry(self)
        self.entry_password = Entry(self, show="*")

        self.label_username.grid(row=0, sticky=E, pady=(10, 1), padx=(10, 1))
        self.label_password.grid(row=1, sticky=E, pady=(1, 3), padx=(10, 1))
        self.entry_username.grid(row=0, column=1, pady=(10, 1), padx=(1, 10))
        self.entry_password.grid(row=1, column=1, pady=(1, 3), padx=(1, 10))

        self.log_btn = Button(self, text="Login", command=self._login_btn_clicked)
        self.log_btn.grid(columnspan=2, pady=(1, 10), padx=(10, 10))

    
    def _login_btn_clicked(self):
        email = self.entry_username.get()
        password = self.entry_password.get()
        if '@' not in email:
            email += '@utcportsmouth.org'
        try:
            self.master.interface.test_login(email, password)
            self.master.enable(self.master.mf.winfo_children())
        except InvalidLoginDetails as e:
            print(e, file=sys.stderr)
            tkm.showerror("Login error", "Incorrect Email or Password")


class MainFrame(LabelFrame):
    def __init__(self, master, controller):
        super().__init__(master)

        self.frame_totalQnum = Frame (self)

        self.label_url = Label(self, text="Enter URL")
        self.entry_url = Entry(self)

        self.label_url.grid(row=0, sticky=E, pady=(10, 1), padx=(10, 1))
        self.entry_url.grid(row=0, column=1, pady=(10, 1), padx=(1, 10))
        
        self.autoSubmit = BooleanVar()
        self.autoSubBtn = Radiobutton(self, 
               text="Auto Submit:",
               variable=self.autoSubmit, 
               value=True,
                command=lambda:self.master.enable(self.frame_totalQnum.winfo_children()))
        self.autoSubBtn.grid(row=1, columnspan=2, sticky=W, pady=(10, 0), padx=(10, 10))


        self.label_totalQnum = Label(self.frame_totalQnum, text="Num. of Qs to Answer")
        self.entry_totalQnum = Entry(self.frame_totalQnum)

        self.label_totalQnum.grid(row=2, column=1, columnspan=1, sticky=W, pady=(0, 1), padx=(1, 10))
        self.entry_totalQnum.grid(row=3, column=1, columnspan=1, pady=(1, 0), padx=(1, 10))

        self.frame_totalQnum.grid(row=3, columnspan=2, pady=(1, 0))


        self.manSubBtn = Radiobutton(self, 
                    text="Manual Submit",
                    variable=self.autoSubmit,               
                    value=False,
                    command=lambda: self.master.disable(self.frame_totalQnum.winfo_children()))
        self.manSubBtn.grid(row=4, columnspan=2, sticky=W, pady=(5, 10), padx=(10, 10))

        
        self.start_btn = Button(self, text="Start", command=self._start_btn_clicked)
        self.start_btn.grid(columnspan=2, pady=(1, 10), padx=(10, 10))

   

    def _start_btn_clicked(self):
        self.url = None
        self.totalQnum = 0
        self.url = self.entry_url.get()
        try:
            if self.autoSubmit.get():
                self.totalQnum = self.entry_totalQnum.get()
                self.totalQnum = int(self.totalQnum)
            self.master.interface.main_loop(self.url, self.totalQnum, self.autoSubmit.get(), self.master)
        except TypeError:
            tkm.showerror("Input error", "Invalid totalQnum")
        




class OutputFrame(LabelFrame):
    def __init__(self, master, controller):
        super().__init__(master)

        self.textbox = Text(self, height=5, width=25)
        self.textbox.configure(state='disabled')
        self.textbox.grid(row=0, column=0)

        scrollb = Scrollbar(self, command=self.textbox.yview)
        scrollb.grid(row=0, column=1, sticky='nsew')
        self.textbox['yscrollcommand'] = scrollb.set

    def write(self, text):
        self.textbox.insert(END, text) 

    def flush(self): # needed for file like object
        pass




class Login():
    def __init__(self):
        print('Ensure that your google acount is NOT linked')
        email = input('Email')
        password = input('Password')
        if '@' not in email:
            email += '@utcportsmouth.org'
        try:
            Interface(email, password)
        except InvalidLoginDetails as e:
            print(e, file=sys.stderr)



class Interface:
    def __init__(self):
        self.session = Session()

    def main_loop(self, url=None, totalQnum=0, autoSubmit = True, root=None):
        handler = AnswerHandler(self.session)
        if url==None:
            print('Press ctrl-c to quit')
            while True:
                url = input('\nType Question url: ')
                res, err = handler.answer_questions_V3(url, autoSubmit)
                if res:
                    print('No more questions for this URL')
                else:
                    print(f'Unexpected exception occurred: {err}', file=sys.stderr)
                    traceback.print_exc()
        else:
            if totalQnum > 0:
                for q in range(1,totalQnum+1): #from 1 to toalt +1 as its q=1 when question_num =1
                    res, err = handler.answer_question_V3(url, autoSubmit)
                    if res:
                        pass
                    else:
                        print(f'Unexpected exception occurred: {err}', file=sys.stderr)
                        traceback.print_exc()
                        break
                    root.update()
                print('Done')

            else:
                res, err = handler.answer_question_V3(url, autoSubmit)
                if res:
                    pass
                else:
                    print(f'Unexpected exception occurred: {err}', file=sys.stderr)
                    traceback.print_exc()

    def test_login(self, email, password):
        login_url = 'https://www.drfrostmaths.com/process-login.php?url='
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                                 ' Chrome/87.0.4280.141 Safari/537.36'}
        data = {'login-email': email, 'login-password': password}

        self.session.post(login_url, headers=headers, data=data, verify=False)
        try:
            """
            verifying user is authenticated by tests if user can load the times tables
            """
            res = self.session.get('https://www.drfrostmaths.com/homework/process-starttimestables.php', verify=False)
            json.loads(res.text)
            
            
        except BaseException:
            raise InvalidLoginDetails(f'Email: {email}, Password: {"*" * len(password)}')






if __name__ == "__main__":
    app = UserInterface()
    sys.stdout = StdoutRedirector(app.of.textbox)
    app.mainloop()
