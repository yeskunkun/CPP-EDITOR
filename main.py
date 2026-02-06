from _tkinter import TclError
from tkinter import Tk,Entry,Toplevel,Label,Button,Frame,Menubutton,Text,Listbox,Menu,BooleanVar,Scrollbar as tkScrollbar
from tkinter import ttk,font
from tkinter.filedialog import askopenfilename,asksaveasfilename
from tkinter.scrolledtext import ScrolledText as Stext
from ctypes import windll,c_uint64,WINFUNCTYPE,c_int,c_long,create_unicode_buffer,sizeof,byref,wintypes
from re import finditer,MULTILINE
from os import _exit,listdir,startfile,kill,remove as delfile
from os.path import dirname,join,exists
from threading import Thread
from winreg import QueryValueEx,OpenKey
from subprocess import run as runcmd,Popen,PIPE,STDOUT,CREATE_NEW_CONSOLE,TimeoutExpired
from sys import argv
from random import randint
from tempfile import gettempdir
from time import sleep,time
from winsound import MessageBeep
isdark = False
windll.user32.CallNextHookEx.argtypes = (wintypes.HHOOK,c_int,wintypes.WPARAM,wintypes.LPARAM)
windll.shell32.SetCurrentProcessExplicitAppUserModelID('editor')
window = Tk()
window.withdraw()
window.showproblem = False
window.appname = 'C++ Editor'
window.title(window.appname)
window.configure(bg='#171717' if isdark else '#F0F0F0')
window.geometry('600x400')
class Scrollbar(tkScrollbar):
    def __init__(self,master,*args,**kwargs):
        super().__init__(master,*args,**kwargs)
        self.orient = kwargs['orient']
        self.menu = Menu(self,tearoff=False)
        if self.orient == 'vertical':
            self.menu.add_command(label='滚动到此处', command=self.scroll_to_click)
            self.menu.add_separator()
            self.menu.add_command(label='顶端对齐',command=self.scroll_to_top)
            self.menu.add_command(label='相对底边对齐',command=self.scroll_to_bottom)
            self.menu.add_separator()
            self.menu.add_command(label='上页',command=self.scroll_up_page)
            self.menu.add_command(label='下页',command=self.scroll_down_page)
            self.menu.add_separator()
            self.menu.add_command(label='向上滚动',command=self.scroll_up)
            self.menu.add_command(label='向下滚动',command=self.scroll_down)
        elif self.orient == 'horizontal':
            self.menu.add_command(label='滚动到此处', command=self.xscroll_to_click)
            self.menu.add_separator()
            self.menu.add_command(label='左端对齐',command=self.scroll_to_left)
            self.menu.add_command(label='右端对齐',command=self.scroll_to_right)
            self.menu.add_separator()
            self.menu.add_command(label='左翻页',command=self.scroll_left_page)
            self.menu.add_command(label='右翻页',command=self.scroll_right_page)
            self.menu.add_separator()
            self.menu.add_command(label='向左滚动',command=self.scroll_left)
            self.menu.add_command(label='向右滚动',command=self.scroll_right)
        self.bind('<Button-3>',self.show_menu)
        self.cpy,self.cpx  = None,None
    def show_menu(self,event):
        self.cpy,self.cpx = event.y,event.x
        self.menu.post(x=event.x_root,y=event.y_root)
        window.after(1,lambda:updatescroll(event))
    def scroll_to_click(self):
        if self.cpy:self.text.yview_moveto(self.cpy/self.winfo_height())
    def xscroll_to_click(self):
        if self.cpx:self.text.xview_moveto(self.cpx/self.winfo_width())
    def scroll_to_top(self):
        self.text.yview_moveto(0)
    def scroll_to_bottom(self):
        self.text.yview_moveto(1)
    def scroll_up_page(self):
        self.text.yview_scroll(-1,'page')
    def scroll_down_page(self):
        self.text.yview_scroll(1,'page')
    def scroll_up(self):
        self.text.yview_scroll(-1,'units')
    def scroll_down(self):
        self.text.yview_scroll(1,'units')
    def scroll_to_left(self):
        self.text.xview_moveto(0)
    def scroll_to_right(self):
        self.text.xview_moveto(1)
    def scroll_left_page(self):
        self.text.xview_scroll(-1,'page')
    def scroll_right_page(self):
        self.text.xview_scroll(1,'page')
    def scroll_left(self):
        self.text.xview_scroll(-1,'units')
    def scroll_right(self):
        self.text.xview_scroll(1,'units')
class LabelStyleMenuButton(Menubutton):
    def __init__(self,master,menu=None,command=None,*args,**kwargs):
        index = kwargs['text'].find('&')+1
        display = ' ' + kwargs['text'].replace('&','') + ' '
        kwargs['text'] = display
        super().__init__(master,bd=0,pady=1,activebackground='#0078D7',activeforeground='#FFFFFF',font=('Microsoft Yahei UI',10),*args,**kwargs)
        if menu:
            self.bind('<ButtonPress-1>',lambda event:menu.post(x=self.winfo_rootx(),y=self.winfo_rooty()+self.winfo_reqheight()) if not compiling else 0)
        else:
            self.bind('<ButtonPress-1>',lambda event:command())
def views(*xy):
    text.yview(*xy)
    linetext.yview(*xy)
def startselectline(self):
    linetext.startline = int(text.index(f'@{self.x},{self.y}').split('.')[0])
    selectline(self,force=True)
    text.focus_set()
def selectline(self,force=False):
    line = int(text.index(f'@{self.x},{self.y}').split('.')[0])
    text.focus_set()
    text.mark_set('insert',f'{line}.0')
    if line != linetext.oldline or force:
        text.tag_remove('sel','1.0','end')
        for i in range(min(linetext.startline,line),max(linetext.startline+1,line+1)):
            text.tag_add('sel',f'{i}.0',f'{i}.end+1c')
        linetext.oldline = line
vsbar = Scrollbar(window,takefocus=False,orient='vertical',borderwidth=0)
text = Text(window,wrap='none',width=99999,height=99999,bg='#131313' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000',yscrollcommand=vsbar.set,insertbackground='#FFFFFF',takefocus=True,borderwidth=0,undo=True)
linetext = Text(window,wrap='none',cursor='arrow',width=0,height=99999,bg='#131313' if isdark else '#FFFFFF',fg='#F0F0F0' if isdark else '#000000',yscrollcommand=vsbar.set,takefocus=False,borderwidth=0)
linetext.count = 0
linetext.startline = 0
linetext.oldline = -1
linetext.update()
linetext.bind('<FocusIn>',lambda _:text.focus_set())
linetext.bind('<MouseWheel>',lambda _:text.yview_moveto(linetext.yview()[0]))
linetext.bind('<ButtonPress-1>',startselectline)
linetext.bind('<B1-Motion>',selectline)
linetext.bind('<<Selection>>',lambda _:text.yview_moveto(vsbar.get()[0]))
vsbar.text = text
text.font = font.Font(window,family='Consolas',size=18,weight='bold')
text.configure(font=text.font)
linetext.configure(font=text.font)
vsbar.configure(command=views)
vsbar.update()
spaces = 0
compiling = False
includesdir = '.'
encode = 'ansi'
file = None
complist = Listbox(window,width=15,bg='#2D2D2D' if isdark else '#EEEEEE',takefocus=False,highlightthickness=0,borderwidth=1,fg='#FFFFFF' if isdark else '#000000',selectbackground='#606060' if isdark else '#AAAAAA',selectforeground='#FFFFFF' if isdark else '#000000',height=6,font=('Microsoft Yahei UI',text.font['size']-6))
complist.bind('<FocusIn>',lambda _:text.focus_set())
window.bind('<ButtonRelease-1>',lambda _:complist.place_forget())
menubar = Frame(window,bg='#171717' if isdark else '#F0F0F0',borderwidth=0,width=99999)
menubar.list = []
##Menu Define##
def saveasfile():
    global file
    road = asksaveasfilename(parent=window,filetypes=[('C++ Source files','*.cpp'),('All files','*')])
    if road:
        road = road.rstrip('.cpp')+'.cpp'
        try:
            with open(road,'w',encoding=encode) as f:
                f.write(text.get('1.0','end-1c'))
        except Exception as e:
            windll.user32.MessageBoxW(0,f'保存失败。\n{type(e).__name__}: {e}',window.title(),16)
        file = road
        window.title(file+' - '+window.appname)
    highlight()
    updatescroll()
    return road
def issavefile():
    updatescroll()
    if file == None and text.get('1.0','end').replace(' ','').replace('\n','') == '':return 0
    ans = windll.user32.MessageBoxW(window.winfo_id(),'是否保存？',window.title(),35)
    if ans == 6:
        savefile()
    elif ans == 7:
        return 0
    else:
        return -1
def openfile(self=None):
    global file
    if not issavefile() == -1:
        road = askopenfilename(parent=window,filetypes=[('C++ Source files','*.cpp'),('All files','*')])
        if road:
            try:
                with open(road,'r',encoding=encode,errors='ignore') as f:
                    content = f.read().rstrip('\n').replace('\t','    ')
                    text.delete('1.0','end')
                    text.insert('end',content)
            except Exception as e:
                return windll.user32.MessageBoxW(0,f'加载失败。\n{type(e).__name__}: {e}',window.title(),16)
            file = road
            window.title(file+' - '+window.appname)
        text.see('insert')
        highlight()
        updatescroll()
        return road
def savefile(self=None):
    global file
    if file:
        try:
            with open(file,'w',encoding=encode) as f:
                f.write(text.get('1.0','end-1c'))
        except Exception as e:
            windll.user32.MessageBoxW(0,f'保存失败。\n{type(e).__name__}: {e}',window.title(),16)
    else:
        saveasfile()
    updatescroll()
def new(self=None):
    global file
    if issavefile() != -1:
        file = None
        text.delete('1.0','end')
        window.title(window.appname)
    highlight()
    updatescroll()
    return file
def exits():
    if issavefile() == -1:
        return 0
    window.destroy()
    _exit(0)
filemenu = Menu(window,tearoff=False,bg='#202020' if isdark else '#FFFFFF',fg='#FFFFFF' if isdark else '#000000')
filemenu.add_command(label='新建(N)    ',underline=3,accelerator='Ctrl+N',command=new)
filemenu.add_command(label='打开(O)    ',underline=3,accelerator='Ctrl+O',command=openfile)
filemenu.add_command(label='保存(S)    ',underline=3,accelerator='Ctrl+S',command=savefile)
filemenu.add_command(label='另存为… (A)    ',underline=5,accelerator='Ctrl+Shift+S',command=saveasfile)
filemenu.add_separator()
filemenu.add_command(label='退出(X)    ',underline=3,accelerator='Alt+F4',command=exits)
def undo(self=None):
    try:
        text.edit_undo()
    except:pass
    highlight(self)
    updatescroll(force=True)
    text.see('insert')
    return 'break'
def redo(self=None):
    try:
        text.edit_redo()
    except:pass
    highlight(self)
    updatescroll(force=True)
    text.see('insert')
    return 'break'
def cut(self=None):
    try:
        ctext = text.get('sel.first','sel.last')
        window.clipboard_clear()
        window.clipboard_append(ctext)
        text.delete('sel.first','sel.last')
    except:pass
    highlight(self)
    updatescroll(force=True)
    text.see('insert')
    return 'break'
def copy(self=None):
    try:
        ctext = text.get('sel.first','sel.last')
        window.clipboard_clear()
        window.clipboard_append(ctext)
    except:pass
    highlight(self)
    updatescroll(force=True)
    text.see('insert')
    return 'break'
def paste(self=None):
    try:
        text.delete('sel.first','sel.last')
    except:pass
    text.insert('insert',window.clipboard_get())
    highlight(self)
    updatescroll(force=True)
    text.see('insert')
    return 'break'
def delete(self=None):
    try:
        text.delete('sel.first','sel.last')
    except:
        text.delete('insert','insert+1c')
    highlight(self)
    updatescroll(force=True)
    text.see('insert')
    return 'break'
def tabtext(self=None):
    global text
    if complist.winfo_ismapped():
        inserts(self)
    else:
        window.after(1,highlight)
        try:
            for i in range(int(text.index('sel.first').split('.')[0]),int(text.index('sel.last+1c').split('.')[0]),1):
                text.insert(f'{i}.0','    ')
        except:
            text.insert('insert','    ')
    updatescroll(force=True)
    text.see('insert')
    return 'break'
def untabtext(self=None):
    global text
    window.after(1,highlight)
    try:
        for i in range(int(text.index('sel.first').split('.')[0]),int(text.index('sel.last+1c').split('.')[0]),1):
            if text.get(f'{i}.0',f'{i}.4') == '    ':
                text.delete(f'{i}.0',f'{i}.4')
    except:
        line = text.index('insert').split('.')[0]
        if text.get(f'{line}.0',f'{line}.4') == '    ':
            text.delete(f'{line}.0',f'{line}.4')
    updatescroll(force=True)
    text.see('insert')
    return 'break'
def comment(self=None):
    global text
    window.after(1,highlight)
    try:
        linef = text.index('sel.first').split('.')[0]
        linel = text.index('sel.last').split('.')[0]
        for i in range(int(linef),int(linel),1):
            finds = text.get(f'{i}.0',f'{i}.end').find('//')
            if text.get(f'{i}.{finds}',f'{i}.{finds+2}') == '//':
                text.delete(f'{i}.{finds}',f'{i}.{finds+2}')
            else:
                text.insert(f'{i}.0','//')
    except:
        line = text.index('insert').split('.')[0]
        finds = text.get(f'{line}.0',f'{line}.end').find('//')
        if text.get(f'{line}.{finds}',f'{line}.{finds+2}') == '//':
            text.delete(f'{line}.{finds}',f'{line}.{finds+2}')
        else:
            text.insert(f'{line}.0','//')
    updatescroll(force=True)
    text.see('insert')
    return 'break'
def autowrap(self=None):
    global wrapvar
    text.configure(wrap='word' if wrapvar.get() else 'none')
    wrapvar.set(wrapvar.get())
    window.after(1,lambda:[update(),updatescroll(force=True),highlight()])
editmenu = Menu(window,tearoff=False,bg='#202020' if isdark else '#FFFFFF',fg='#FFFFFF' if isdark else '#000000')
editmenu.add_command(label='撤销(U)    ',underline=3,accelerator='Ctrl+Z',command=undo)
editmenu.add_command(label='复原(R)    ',underline=3,accelerator='Ctrl+Shift+Z',command=redo)
editmenu.add_separator()
editmenu.add_command(label='剪切(T)    ',underline=3,accelerator='Ctrl+X',command=cut)
editmenu.add_command(label='复制(C)    ',underline=3,accelerator='Ctrl+C',command=copy)
editmenu.add_command(label='粘贴(P)    ',underline=3,accelerator='Ctrl+V',command=paste)
editmenu.add_command(label='删除(D)    ',underline=3,accelerator='Delete',command=delete)
editmenu.add_separator()
editmenu.add_command(label='全部选中(A)    ',underline=5,accelerator='Ctrl+A',command=lambda:text.tag_add('sel','1.0','end'))
editmenu.add_separator()
editmenu.add_command(label='缩进行    ',accelerator='Tab',command=tabtext)
editmenu.add_command(label='移除缩进    ',accelerator='Shift+Tab',command=untabtext)
editmenu.add_command(label='注释或取消注释行    ',accelerator='Ctrl+/',command=comment)
editmenu.add_separator()
wrapvar = BooleanVar()
wrapvar.set(False)
editmenu.add_checkbutton(label='自动换行',variable=wrapvar,command=autowrap)
tempmenu = Menu(window,tearoff=False,bg='#202020' if isdark else '#FFFFFF',fg='#FFFFFF' if isdark else '#000000')
def __insertconsoletemplate(self=None):
    text.delete('1.0','end')
    text.insert('end','''#include <iostream>
#include <algorithm>
#include <cmath>
#include <iomanip>
using namespace std;

int main() {
'''+'    '+'''
    return 0;
}''')
    text.mark_set('insert','8.4')
    window.after(1,lambda:[highlight(),updatescroll(force=False)])
def __insertwindowstemplate(self=None):
    text.delete('1.0','end')
    text.insert('end','''#include <windows.h>
WNDCLASSEXA wc;
HWND hwnd;
MSG msg;
int main() {
    wc.cbSize = sizeof(WNDCLASSEXA);
    wc.lpfnWndProc = [](HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam) {
        switch (msg) {
        case WM_DESTROY: {
            PostQuitMessage(0);
            break;
        }
        }
        return DefWindowProcA(hwnd, msg, wparam, lparam); };
    wc.hInstance = GetModuleHandleA(0);
    wc.hCursor = LoadCursorA(0, IDC_ARROW);
    wc.lpszClassName = "WindowClass";
    RegisterClassExA(&wc);
    hwnd = CreateWindowExA(257, "WindowClass", "", WS_OVERLAPPEDWINDOW | WS_VISIBLE, CW_USEDEFAULT, CW_USEDEFAULT, 800, 600, 0, 0, 0, 0);
    while (GetMessageA(&msg, 0, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageA(&msg);
    }
    return msg.wParam;
}''')
    text.mark_set('insert','19.48')
    text.see('19.48')
    window.after(1,lambda:[highlight(),updatescroll(force=False)])
tempmenu.add_command(label='插入经典控制台头文件模板    ',accelerator='Alt+1',command=__insertconsoletemplate)
tempmenu.add_separator()
tempmenu.add_command(label='插入 Windows API 窗口模板    ',accelerator='Alt+2',command=__insertwindowstemplate)
def compiles(self=None):
    global file,compiling
    updatescroll()
    if file:
        if savefile() == -1:return -1
        if exists(file.rstrip('.cpp')+'.exe'):delfile(file.rstrip('.cpp')+'.exe')
        compiling = True
        gccdir = join(dirname(argv[0]),'mingw64\\bin\\g++.exe')
        try:
            process = Popen(['g++',file.replace('/','\\'),'-o',file.replace('/','\\').rstrip('.cpp')+'.exe','-static'],stdout=PIPE,stderr=STDOUT,text=True,bufsize=1,universal_newlines=True,encoding='utf-8',errors='ignore')
        except Exception:
            try:
                process = Popen([gccdir,file.replace('/','\\'),'-o',file.replace('/','\\').rstrip('.cpp')+'.exe','-static'],cwd=dirname(gccdir),stdout=PIPE,stderr=STDOUT,text=True,bufsize=1,universal_newlines=True,encoding='utf-8',errors='ignore')
            except Exception:
                return downloadgcc()
        error,warning,ew = '','',0
        while process.poll() is None:
            try:
                line = process.stdout.readline()
            except UnicodeDecodeError:
                line = ''
            if line:
                if 'error: ' in line or 'ld.exe: ' in line:
                    error += line.strip()+'\n'
                    ew += 1
                if 'warning: ' in line:
                    warning += line.strip()+'\n'
                    ew += 1
                print(line)
                if ew >= 50:
                    print('\n警告和错误总数超过50条，为防止程序崩溃，编译中止。\n')
                    process.terminate()
                    process.kill()
                    break
        compiling = False
        if not error and not exists(file.replace('/','\\').rstrip('.cpp')+'.exe'):
            return windll.user32.MessageBoxW(window.winfo_id(),f'{process.stdout.read()}','错误',16)
        if warning:
            if windll.user32.MessageBoxW(window.winfo_id(),f'{warning}\n\n是否继续运行？',f'警告',49) == 2:
                return 2
        if error or not exists(file.replace('/','\\').rstrip('.cpp')+'.exe'):
            return windll.user32.MessageBoxW(window.winfo_id(),f'{error}','错误',16)
    else:
        if issavefile() in [-1,0]:
            return -1
        else:
            compiles(self)
def execute(file,temp=False,args=[]):
    updatescroll()
    tmp = window.state()
    window.state('iconic')
    currdir = join(dirname(__file__),'ConsolePauser.exe')
    runcmd([currdir,file.rstrip('.cpp')+'.exe']+args,creationflags=CREATE_NEW_CONSOLE)
    if temp:
        for i in range(3):
            try:
                if exists(file.rstrip('.cpp')+'.exe'):
                    delfile(file.rstrip('.cpp')+'.exe')
                    break
            except PermissionError:
                sleep(0.1)
    window.state(tmp)
    window.deiconify()
    window.update_idletasks()
    windll.user32.SetForegroundWindow(windll.user32.GetParent(window.winfo_id()))
    window.focus_set()
    text.focus_set()
def run(self=None,args=[]):
    if file:
        if exists(file):
            if exists(file.rstrip('.cpp')+'.exe'):
                Thread(target=execute,args=(file,False,args),daemon=False).start()
            else:
                compiles(self)
        else:
            if issavefile() in [-1,0]:
                return -1
            else:
                run(self)
def compilerunintemp(self=None,args=[]):
    updatescroll()
    filet = join(gettempdir(),f'{randint(0,9)}{randint(0,9)}{randint(0,9)}{randint(0,9)}{randint(0,9)}{randint(0,9)}{randint(0,9)}{randint(0,9)}{randint(0,9)}{randint(0,9)}.cpp')
    try:
        with open(filet,'w',encoding=encode) as f:f.write(text.get('1.0','end-1c'))
    except:
        return windll.user32.MessageBoxW(0,f'保存失败。\n{type(e).__name__}: {e}',window.title(),16)
    compiling = True
    gccdir = join(dirname(argv[0]),'mingw64\\bin\\g++.exe')
    try:
        process = Popen(['g++',filet.replace('/','\\'),'-o',filet.replace('/','\\').rstrip('.cpp')+'.exe','-static'],stdout=PIPE,stderr=STDOUT,text=True,bufsize=1,universal_newlines=True)
    except:
        try:
            process = Popen([gccdir,filet.replace('/','\\'),'-o',filet.replace('/','\\').rstrip('.cpp')+'.exe','-static'],cwd=dirname(gccdir),stdout=PIPE,stderr=STDOUT,text=True,bufsize=1,universal_newlines=True)
        except Exception:
            return downloadgcc()
    error,warning,ew = '','',0
    while process.poll() is None:
        line = process.stdout.readline()
        if line:
            if 'error: ' in line or 'ld.exe: ' in line:
                error += line.strip()+'\n'
                ew += 1
            if 'warning: ' in line:
                warning += line.strip()+'\n'
                ew += 1
            print(line)
            if ew >= 50:
                print('\n警告和错误总数超过50条，为防止程序崩溃，编译中止。\n')
                process.terminate()
                process.kill()
                break
    compiling = False
    if not error and not exists(filet.replace('/','\\').rstrip('.cpp')+'.exe'):
        return windll.user32.MessageBoxW(window.winfo_id(),f'{process.stdout.read()}','编译出错。',16)
    if warning:
        if windll.user32.MessageBoxW(window.winfo_id(),f'{warning}\n\n是否继续运行？',f'编译警告。',49) == 2:
            return 2
    if error or not exists(filet.replace('/','\\').rstrip('.cpp')+'.exe'):
        return windll.user32.MessageBoxW(window.winfo_id(),f'{error}',f'编译出错。',16)
    try:
        delfile(filet)
        Thread(target=execute,args=(filet,True,args),daemon=False).start()
    except OSError:
        pass
def compilerun(self=None):
    if self:
        if not file:        
            return compilerunintemp()
    if compiles() != -1:
        run()
compmenu = Menu(window,tearoff=False,bg='#202020' if isdark else '#FFFFFF',fg='#FFFFFF' if isdark else '#000000')
compmenu.add_command(label='编译(C)    ',underline=3,accelerator='F9',command=compiles)
compmenu.add_command(label='运行(R)    ',underline=3,accelerator='F10',command=run)
compmenu.add_command(label='编译并运行(E)    ',underline=6,accelerator='F11, F5',command=compilerun)
compmenu.add_command(label='在临时目录编译并运行(T)    ',underline=11,accelerator='    ',command=compilerunintemp)
def run_process_with_input(command, input_text, timeout=None):
    """
    运行命令并自动输入内容
    
    Args:
        command: 要执行的命令（字符串或列表）
        input_text: 要输入到stdin的内容
        timeout: 超时时间（秒）
    
    Returns:
        (returncode, stdout, stderr)
    """
    try:
        # 如果命令是字符串，可以转换为列表（可选）
        if isinstance(command, str):
            # 使用shlex.split处理带引号的参数
            command = shlex.split(command)
        
        # 启动进程
        
        # 发送输入并获取输出，设置超时
        stdout, stderr = proc.communicate(input=input_text, timeout=timeout)
        return proc.returncode, stdout, stderr
        
    except subprocess.TimeoutExpired:
        proc.kill()  # 杀死进程
        stdout, stderr = proc.communicate()  # 清理
        raise TimeoutError(f"命令执行超时（{timeout}秒）")
    except Exception as e:
        raise e
class Problem:
    def __init__(self,master):
        self.master = master
        self.width = width = 220
        self.problem = Frame(master,bg='#171717' if isdark else '#F0F0F0',width=width,height=99999,borderwidth=0)
        self.controls = []
        self.controls.append(Label(self.problem,text='题目描述',anchor='nw',font=('微软雅黑',15)))
        self.controls[0].place(x=0,y=0,width=width,height=33)
        self.controls.append(Stext(self.problem,borderwidth=0,font=('微软雅黑',13)))
        self.controls[1].place(x=4,y=33,width=width-8,height=117)
        self.controls[1].bind('<Control-V>',self.paste)
        self.controls[1].bind('<Control-v>',self.paste)
        self.controls.append(Label(self.problem,text='输入样例',anchor='nw',font=('微软雅黑',15)))
        self.controls[2].place(x=0,y=0+150,width=width-20,height=33)
        self.controls.append(Stext(self.problem,borderwidth=0,font=('Consolas',12)))
        self.controls[3].place(x=4,y=33+150,width=width-8,height=60)
        self.controls.append(Label(self.problem,text='输出样例',anchor='nw',font=('微软雅黑',15)))
        self.controls[4].place(x=0,y=0+250,width=width,height=33)
        self.controls.append(Stext(self.problem,borderwidth=0,font=('Consolas',12)))
        self.controls[5].place(x=4,y=33+250,width=width-8,height=60)
        self.controls.append(Button(self.problem,text='复制',takefocus=False,command=lambda:[window.clipboard_clear(),
        window.clipboard_append(self.controls[3].get('1.0','end-1c')),self.controls[6].configure(text='成功'),
        window.after(1000,lambda:self.controls[6].configure(text='复制'))],borderwidth=0,font=('微软雅黑',11)))
        self.controls[6].place(x=width-50,y=0+150,width=50,height=33)
        self.controls.append(Button(self.problem,text='运行',takefocus=False,command=self.judge,borderwidth=0,font=('微软雅黑',11)))
        self.controls[7].place(x=width-50,y=0+250,width=50,height=33)
##        self.controls.append()
    def paste(self,event=None):
        try:
            self.controls[1].delete('sel.first','sel.last')
        except:pass
        self.controls[1].insert('insert',self.master.clipboard_get().replace('\n',''))
        self.controls[1].see('insert')
        return 'break'
    def execute(self,file,temp=False):
        currdir = join(dirname(__file__),'ConsolePauser.exe')
        try:
            proc = Popen(file.rstrip('.cpp')+'.exe',stdin=PIPE,stdout=PIPE,stderr=PIPE,text=True,encoding='utf-8',universal_newlines=True)
            stdout,stderr = proc.communicate(input=self.controls[3].get('1.0','end'),timeout=1)
            tar = self.controls[5].get('1.0','end-1c').replace('\n',' ').replace('\t',' ').rstrip(' ')
            out = stdout.replace('\n',' ').replace('\t',' ').rstrip(' ')
            if tar == out:
                windll.user32.MessageBoxW(window.winfo_id(),'Accepted','Successfully',64)
            else:
                windll.user32.MessageBoxW(window.winfo_id(),'Wrong Answer','Error',16)
        except TimeoutExpired:
            windll.user32.MessageBoxW(window.winfo_id(),'Time Limit Exceed','Error',16)
        proc.kill()
        if temp:
            for i in range(3):
                try:
                    if exists(file.rstrip('.cpp')+'.exe'):
                        delfile(file.rstrip('.cpp')+'.exe')
                        break
                except PermissionError:
                    sleep(0.1)
    def judge(self,event=None):
        updatescroll()
        filet = join(gettempdir(),f'{randint(0,9)}{randint(0,9)}{randint(0,9)}{randint(0,9)}{randint(0,9)}{randint(0,9)}{randint(0,9)}{randint(0,9)}{randint(0,9)}{randint(0,9)}.cpp')
        try:
            with open(filet,'w',encoding=encode) as f:f.write(text.get('1.0','end-1c'))
        except:
            return windll.user32.MessageBoxW(0,f'保存失败。\n{type(e).__name__}: {e}',window.title(),16)
        compiling = True
        gccdir = join(dirname(argv[0]),'mingw64\\bin\\g++.exe')
        try:
            process = Popen(['g++',filet.replace('/','\\'),'-o',filet.replace('/','\\').rstrip('.cpp')+'.exe','-static'],stdout=PIPE,stderr=STDOUT,text=True,bufsize=1,universal_newlines=True)
        except:
            try:
                process = Popen([gccdir,filet.replace('/','\\'),'-o',filet.replace('/','\\').rstrip('.cpp')+'.exe','-static'],cwd=dirname(gccdir),stdout=PIPE,stderr=STDOUT,text=True,bufsize=1,universal_newlines=True)
            except Exception:
                return downloadgcc()
        error,warning,ew = '','',0
        while process.poll() is None:
            line = process.stdout.readline()
            if line:
                if 'error: ' in line or 'ld.exe: ' in line:
                    error += line.strip()+'\n'
                    ew += 1
                if 'warning: ' in line:
                    warning += line.strip()+'\n'
                    ew += 1
                print(line)
                if ew >= 50:
                    print('\n警告和错误总数超过50条，为防止程序崩溃，编译中止。\n')
                    process.terminate()
                    process.kill()
                    break
        compiling = False
        if not error and not exists(filet.replace('/','\\').rstrip('.cpp')+'.exe'):
            return windll.user32.MessageBoxW(window.winfo_id(),f'Compile Error','Error',16)
        if error or not exists(filet.replace('/','\\').rstrip('.cpp')+'.exe'):
            return windll.user32.MessageBoxW(window.winfo_id(),f'Compile Error',f'Error',16)
        try:
            delfile(filet)
            Thread(target=self.execute,args=(filet,True),daemon=False).start()
        except OSError:
            pass
p = Problem(window)
def updatepack(self=None):
    p.problem.pack_forget()
    text.pack_forget()
    menubar.pack_forget()
    vsbar.pack_forget()
    bottombox.pack_forget()
    linetext.pack_forget()
    complist.configure(font=('Microsoft Yahei UI',text.font['size']-6))
    menubar.pack(side='top',fill='x',expand=True)
    bottombox.pack(side='bottom',fill='x',expand=True)
    if window.showproblem:
        p.problem.pack(side='right',fill='y',expand=True)
    vsbar.pack(side='right',fill='y',expand=True)
    linetext.pack(side='left',fill='y',expand=True)
    text.pack(fill='both',expand=True)
def setproblem(self=None):
    global window
    show = window.showproblem
    window.showproblem = not show
    if window.showproblem:
        window.geometry(f'{window.winfo_width()+p.width}x{window.winfo_height()}')
    else:
        window.geometry(f'{window.winfo_width()-p.width}x{window.winfo_height()}')
    updatepack()
ojmenu = Menu(window,tearoff=False,bg='#202020' if isdark else '#FFFFFF',fg='#FFFFFF' if isdark else '#000000')
ojmenu.add_command(label='设置题目(S)    ',underline=5,accelerator='F3',command=setproblem)
ojmenu.add_separator()
ojmenu.add_command(label='自动判题(A)    ',underline=5,accelerator='F4',command=p.judge)
def hook_callback(nCode,wParam,lParam):
    if nCode == 5:
        hwnd = wParam
        class_name = create_unicode_buffer(256)
        windll.user32.GetClassNameW(hwnd,class_name,256)
        if class_name.value == '#32770':
            h_button = windll.user32.FindWindowExW(hwnd,None,'Button',None)
            button_texts = ['网站','关闭']
            index = 0
            while h_button and index < len(button_texts):
                windll.user32.SetWindowTextW(h_button,button_texts[index])
                index += 1
                h_button = windll.user32.FindWindowExW(hwnd,h_button,'Button',None)
    return windll.user32.CallNextHookEx(None,nCode,wParam,lParam)
hook_proc = WINFUNCTYPE(wintypes.LPARAM,c_int,wintypes.WPARAM,wintypes.LPARAM)(hook_callback)
def show_help(self=None):
    h_hook = windll.user32.SetWindowsHookExW(5,hook_proc,None,windll.kernel32.GetCurrentThreadId())
    if windll.user32.MessageBoxExW(window.winfo_id(),'''C++编辑器。
野生坤坤没头像制作。
http://www.yeskunkun.cn/

收到求助，将通知老师。''',f'关于',65,0x00000904) == 1:
        startfile('http://www.yeskunkun.cn/')
    windll.user32.UnhookWindowsHookEx(h_hook)
def downloadgcc(self=None):
    toplevel = Toplevel(window)
    window.bell()
    toplevel.withdraw()
    toplevel.transient(window)
    toplevel.resizable(0,0)
    toplevel.geometry(f'600x400+200+200')
    toplevel.title(f'下载MinGW-Win64 - {window.appname}')
    toplevel.configure(bg='#171717' if isdark else '#F0F0F0')
    Label(toplevel,bg=toplevel['bg'],fg='#FFFFFF' if isdark else '#000000',text='下载MinGW-Win64',font=('Microsoft Yahei UI',17)).pack(pady=2)
    Frame(toplevel,bg=toplevel['bg'],width=0,height=0).pack(side='bottom',pady=4)
    Button(toplevel,text='关闭',width=99999,bg='#202020' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000',activebackground='#602020' if isdark else '#FFFFFF',activeforeground='#FFFFFF' if isdark else '#000000',command=lambda:[window.attributes('-disabled',False),toplevel.destroy(),window.focus_force()],font=('Microsoft Yahei UI',12)).pack(side='bottom',fill='x',padx=10,pady=2)
    Button(toplevel,text='前往',width=99999,bg='#202020' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000',activebackground='#602020' if isdark else '#FFFFFF',activeforeground='#FFFFFF' if isdark else '#000000',command=lambda:startfile('https://github.com/niXman/mingw-builds-binaries/releases/'),font=('Microsoft Yahei UI',12)).pack(side='bottom',fill='x',padx=10,pady=2)
    vsbars = Scrollbar(toplevel,orient='vertical')
    texts = Text(toplevel,width=99999,height=99999,yscrollcommand=vsbars.set,bd=0,bg='#171717' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000',insertbackground='#FFFFFF' if isdark else '#000000',font=text.font)
    texts.insert('end','''前往 https://github.com/niXman/mingw-builds-binaries/releases/ ？

如果需要使用编辑器的编译功能，请下载MinGW-Win64。
MinGW中包括G++和GCC编译器，此编辑器的编译依赖此功能。

如果你安装了MinGW-Win64，请指定GCC和G++的系统环境变量。
如果文件缺失，你看到此提示，请前往下载并补全文件。
在即将打开的页面中，寻找最新的MinGW-Win64二进制工程，寻找“资产”字样，
并在列表中单击“x86_64-*.*.*-release-win32-seh-msvcrt-*”。
等待下载完成，打开压缩包，将mingw64文件夹放入本程序的所在目录即可。
如果遇到无法连接网站的情况，请过一会再尝试，或者下载Watt Toolkit（Steam++）加速器。''')
    vsbars.configure(command=texts.yview)
    vsbars.update()
    windll.uxtheme.SetWindowTheme(vsbars.winfo_id(),'DarkMode_Explorer' if isdark else 0,0)
    vsbars.text = texts
    vsbars.menu.configure(bg='#202020' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000')
    vsbars.pack(side='right',fill='y')
    texts.pack(fill='both',expand=True,padx=10,pady=10)
    toplevel.update()
    windll.dwmapi.DwmSetWindowAttribute(windll.user32.GetParent(toplevel.winfo_id()),20,byref(c_int(True)),sizeof(c_int))
    windll.dwmapi.DwmSetWindowAttribute(windll.user32.GetParent(toplevel.winfo_id()),35,byref(c_int(0x171717 if isdark else 0xF0F0F0)),sizeof(c_int))
    windll.user32.SendMessageW(windll.user32.GetParent(toplevel.winfo_id()),274,61472,0)
    windll.user32.SendMessageW(windll.user32.GetParent(toplevel.winfo_id()),274,61728,0)
    window.attributes('-disabled',True)
    toplevel.protocol('WM_DELETE_WINDOW',lambda:[window.attributes('-disabled',False),toplevel.destroy(),window.focus_force()])
    toplevel.focus_force()
    window.wait_window(toplevel)
helpmenu = Menu(window,tearoff=False,bg='#202020' if isdark else '#FFFFFF',fg='#FFFFFF' if isdark else '#000000')
helpmenu.add_command(label='救命(A)    ',underline=3,accelerator='F1',command=show_help)
helpmenu.add_separator()
helpmenu.add_command(label='下载MinGW-Win64    ',accelerator='    ',command=downloadgcc)
helpmenu.add_separator()
helpmenu.add_command(label='野生坤坤没头像个人网页    ',accelerator='    ',command=lambda:startfile('http://www.yeskunkun.cn/'))
##############
menubar.list.append(LabelStyleMenuButton(menubar,text='文件(&F)',menu=filemenu))
menubar.list.append(LabelStyleMenuButton(menubar,text='编辑(&E)',menu=editmenu))
menubar.list.append(LabelStyleMenuButton(menubar,text='模板(&T)',menu=tempmenu))
menubar.list.append(LabelStyleMenuButton(menubar,text='编译(&C)',menu=compmenu))
menubar.list.append(LabelStyleMenuButton(menubar,text='&OJ',menu=ojmenu))
menubar.list.append(LabelStyleMenuButton(menubar,text='帮助(&A)',menu=helpmenu))
for i in menubar.list:
    i.pack(side='left')
def fullscreen():
    menubar.list[6].destroy()
    menubar.list[6] = LabelStyleMenuButton(menubar,text='置顶' if window.attributes('-topmost') else '取消置顶',command=fullscreen)
    menubar.list[6].pack(side='right')
    window.attributes('-topmost',not window.attributes('-topmost'))
    update(force=True)
    highlight()
menubar.list.append(LabelStyleMenuButton(menubar,text='置顶',command=fullscreen))
menubar.list[len(menubar.list)-1].pack(side='right')
menubar.pack(side='top',fill='x',expand=True)
bottombox = Frame(window,bg='#171717' if isdark else '#F0F0F0',borderwidth=0,width=99999)
szgrip = ttk.Sizegrip(bottombox,style='TSizegrip',takefocus=False)
szgrip.style = ttk.Style(window)
szgrip.style.configure('TSizegrip',background='#171717' if isdark else '#F0F0F0',borderwidth=0)
szgrip.pack(side='right',fill='y')
hsbar = Scrollbar(bottombox,takefocus=False,orient='horizontal',borderwidth=0)
text.configure(xscrollcommand=hsbar.set)
hsbar.text = text
hsbar.configure(command=text.xview)
hsbar.pack(fill='x',expand=True)
bottombox.pack(side='bottom',fill='x',expand=True)
vsbar.pack(side='right',fill='y',expand=True)
linetext.pack(side='left',fill='y',expand=True)
def getspace(self=None):
    global spaces
    ls = text.get('1.0','insert').count('{')
    rs = text.get('1.0','insert').count('}')
    spaces = ls-rs+1
    return spaces
def updatescroll(self=None,force=False):
    count = int(text.index('end').split('.')[0]) - 1
    if count != linetext.count or force:
        line_contents = []
        for i in range(count):
            line_contents.append(f' {i+1}')
            line_contents.extend('\n'*text.count(f'{i+1}.0',f'{i+1}.end','displaychars','displaylines')[1])
            if i != count - 1:
                line_contents.append('\n')
            linetext.configure(state='normal')
        linetext.delete('1.0','end')
        linetext.insert('end',''.join(line_contents))
        linetext.configure(width=max(4, len(str(count)) + 2))
        linetext.configure(state='disabled')
        linetext.count = count
    linetext.yview_moveto(vsbar.get()[0])
    text.yview_moveto(vsbar.get()[0])
##    text.focus_set()
def getvisibleline():
    return ('1.0','end-1c')
def highlight(self=None):
    global text,linetext
    linetext.yview_moveto(text.yview()[0])
    visibleline = getvisibleline()
    if visibleline:
        for i in ['red','green','yellow','blue','orange','purple','grey']:
            text.tag_remove(i,visibleline[0],visibleline[1])
        for pattern, tag in ((r'#.*$','red'),(r'(//.*$)|(/\*.*?\*/)','grey'),
                                        (r'\b(try|catch|switch|typedef|if|else|case|default|public|protected|private|for|do|while|return|int|break|continue|char|float|double|bool|void|auto|short|long|signed|static|unsigned)\b','yellow'),
                                        (r'\b(class|struct|using|delete|typename|sizeof|const|volatile|operator|namespace)\b','blue'),
                                        (r'\b(new|true|false|NULL)\b','orange'),(r'\b\d+\b','purple'),(r'(".*?(?:"|$)|".*")|(\'.*?(?:\'|$)|\'.*\')','green')):
            matches = finditer(pattern,text.get(visibleline[0],visibleline[1]),MULTILINE)
            for i in matches:
                if tag == 'green':
                    for j in ['red','yellow','blue','orange','purple']:
                        Thread(target=text.tag_remove,args=(j,f'1.0+{i.start()}c',f'1.0+{i.end()}c'),daemon=True).start()
                text.tag_add(tag,f'1.0+{i.start()}c',f'1.0+{i.end()}c')
def update(self=None,force=False):
    global isdark
    oisdark = isdark
    try:
        isdark = not QueryValueEx(OpenKey(18446744071562067969,r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize'),'AppsUseLightTheme')[0]
    except FileNotFoundError:
        isdark = False
    if isdark != oisdark or force:
        windll.dwmapi.DwmSetWindowAttribute(windll.user32.GetParent(window.winfo_id()),20,byref(c_int(True)),sizeof(c_int))
        windll.dwmapi.DwmSetWindowAttribute(windll.user32.GetParent(window.winfo_id()),35,byref(c_int(0x171717 if isdark else 0xF0F0F0)),sizeof(c_int))
        getspace()
        szgrip.style.configure('TSizegrip',background='#171717' if isdark else '#F0F0F0',borderwidth=0)
        windll.uxtheme.SetWindowTheme(vsbar.winfo_id(),'DarkMode_Explorer' if isdark else 0,0)
        vsbar.menu.configure(bg='#202020',fg='#FFFFFF')
        windll.uxtheme.SetWindowTheme(hsbar.winfo_id(),'DarkMode_Explorer' if isdark else 0,0)
        hsbar.menu.configure(bg='#202020',fg='#FFFFFF')
        for i in p.controls:
            try:
                windll.uxtheme.SetWindowTheme(i.vbar.winfo_id(),'DarkMode_Explorer' if isdark else 0,0)
            except AttributeError:pass
            try:
                i.configure(bg='#171717' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000',insertbackground='#FFFFFF' if isdark else '#000000')
            except TclError:
                try:
                    i.configure(bg='#171717' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000')
                except TclError:
                    i.configure(bg='#171717' if isdark else '#F0F0F0')
        p.problem.configure(bg='#171717' if isdark else '#F0F0F0')
        text.tag_configure('red',foreground='#FF4040' if isdark else '#F02020')
        text.tag_configure('green',foreground='#40FF40' if isdark else '#20AA20')
        text.tag_configure('yellow',foreground='#FFFF40' if isdark else '#CCCC00')
        text.tag_configure('blue',foreground='#4040F0' if isdark else '#2020F0')
        text.tag_configure('orange',foreground='#FFAA40' if isdark else '#FFAA20')
        text.tag_configure('purple',foreground='#BEB7FF' if isdark else '#B097EA')
        text.tag_configure('grey',foreground='#999999' if isdark else '#555555')
        filemenu.configure(bg='#202020' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000')
        editmenu.configure(bg='#202020' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000')
        tempmenu.configure(bg='#202020' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000')
        compmenu.configure(bg='#202020' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000')
        ojmenu.configure(bg='#202020' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000')
        helpmenu.configure(bg='#202020' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000')
        complist.configure(bg='#2D2D2D' if isdark else '#E0E0E0',fg='#FFFFFF' if isdark else '#000000',selectbackground='#606060' if isdark else '#AAAAAA',selectforeground='#FFFFFF' if isdark else '#000000')
        window.configure(bg='#171717' if isdark else '#F0F0F0')
        menubar.configure(bg='#171717' if isdark else '#F0F0F0')
        for i in menubar.list:
            i.configure(bg='#171717' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000')
        text.configure(bg='#171717' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000',insertbackground='#FFFFFF' if isdark else '#000000')
        linetext.configure(bg='#171717' if isdark else '#FFFFFF',fg='#AAAAAA' if isdark else '#888888')
    updatescroll()
def update_thread():
    update()
    window.after(2000,update_thread)
def inserts(self):
    selection = complist.curselection()
    if not selection:
        selection = [0]
    selected = complist.get(selection[0])
    current_pos = text.index('insert')
    line,col = map(int,current_pos.split('.'))
    line_text = text.get(f'{line}.0',f'{line}.end')
    word_start = col
    while word_start > 0 and line_text[word_start-1].isalpha():
        word_start -= 1
    text.delete(f'{line}.{word_start}',current_pos)
    text.insert(f'{line}.{word_start}',selected)
    complist.place_forget()
    highlight(self)
    updatescroll(force=True)
    return 'break'
complist.bind('<ButtonRelease-1>',inserts)
def completion(self):
    complist.delete(0,'end')
    complist.place_forget()
    line,col = map(int,text.index('insert').split('.'))
    line_text = text.get(f'{line}.0',f'{line}.end')
    word_start = col
    while word_start > 0 and line_text[word_start-1].isalpha():
        word_start -= 1
    current_word = line_text[word_start:col]
    if text.get(f'{line}.0',f'{line}.1') == '#':
        if text.get(f'{line}.0',f'{line}.8') == '#include' or text.get(f'{line}.0',f'{line}.9') == '#include ':return 0
        suggestions = [i for i in ('define','elif','elifdef','elifndef','else','endif','error','if','ifdef','ifndef','import','include','line','pragma','region','undef','using','warning') if i.startswith(current_word)]
    else:
        suggestions = [i for i in ('true','false','NULL','nullptr','typedef','int','char','float','double','bool','void','short','long','signed','unsigned','static','if','else','switch','case','default','while','do','for','break','continue','return','public','protected','private','class','struct','union','new','delete','typename','try','catch','using','namespace','sizeof','const','volatile','operator') if i.startswith(current_word)]
    if current_word or text.get(f'{line}.0',f'{line}.1') == '#':
        line = text.index('insert').split('.')[0]
        if suggestions:
            for i in suggestions:
                complist.insert('end',i)
                try:
                    x,y,_,_ = text.bbox(text.index('insert'))
                except TypeError:
                    return 1
                if x and y:
                    complist.place(x=x+linetext.winfo_width(),y=y+text.font.metrics('linespace')+menubar.winfo_height())
                else:
                    complist.delete(0,'end')
                    complist.place_forget()
        else:
            complist.delete(0,'end')
            complist.place_forget()
    else:
        complist.delete(0,'end')
        complist.place_forget()
def typing(self):
    global text,spaces
    if self.char:
        text.see('insert')
    complist.delete(0,'end')
    window.after(1,lambda:[highlight(self),completion(self),updatescroll(self,force=False)])
    if self.char in ['#','"']:
        completion(self)
    if self.char == '(':
        text.insert('insert',')')
        text.mark_set('insert','insert-1c')
    if self.char == '[':
        text.insert('insert',']')
        text.mark_set('insert','insert-1c')
    if self.char == '{':
        text.insert('insert','}')
        text.mark_set('insert','insert-1c')
    if self.char == '<' and text.get('insert','insert+1c') != '>' and '#include' in text.get('insert-9c','insert'):
        text.insert('insert','>')
        text.mark_set('insert','insert-1c')
    if self.char == ')' and text.get('insert','insert+1c') == ')' and text.get('insert-1c','insert') == '(':
        text.mark_set('insert','insert+1c')
        return 'break'
    if self.char == ']' and text.get('insert','insert+1c') == ']' and text.get('insert-1c','insert') == '[':
        text.mark_set('insert','insert+1c')
        return 'break'
    if self.char == '}':
        text.mark_set('insert','insert+1c')
        return 'break'
    if self.char == '>' and text.get('insert','insert+1c') == '>' and text.get('insert-1c','insert') == '<':
        text.mark_set('insert','insert+1c')
        return 'break'
def deltext(self):
    global text
    getspace()
    window.after(1,lambda:[highlight(self),completion(self),updatescroll(self)])
    try:
        text.delete('sel.first','sel.last')
    except (IndexError,TypeError,TclError):
        if text.get('insert-4c','insert') == '    ':
            text.delete('insert-4c','insert')
        elif text.get('insert-1c','insert') == '(' and text.get('insert','insert+1c') == ')':
            text.delete('insert-1c','insert+1c')
        elif text.get('insert-1c','insert') == '[' and text.get('insert','insert+1c') == ']':
            text.delete('insert-1c','insert+1c')
        elif text.get('insert-1c','insert') == '{' and text.get('insert','insert+1c') == '}':
            text.delete('insert-1c','insert+1c')
        elif text.get('insert-1c','insert') == '<' and text.get('insert','insert+1c') == '>':
            text.delete('insert-1c','insert+1c')
        else:
            text.delete('insert-1c','insert')
    return 'break'
def rettext(self):
    global text,spaces
    getspace()
    window.after(1,lambda:[highlight(self),completion(self),updatescroll(self,force=True)])
    try:
        text.delete('sel.first','sel.last')
    except:pass
    if text.get('insert-1c','insert') == '{':
        if text.get('insert','insert+1c') == '}':
            getspace()
            text.insert('insert',('\n'+((spaces-2)*'    ') if (spaces-2) >= 0 else ''))
            text.mark_set('insert',f'insert-{(spaces-2)*4+1}c')
    getspace()
    text.insert('insert','\n'+(((spaces-1)*'    ') if (spaces-1) >= 0 else ''))
    text.see('insert')
    return 'break'
def resize(event):
    window.after(1,lambda:[highlight(event),updatescroll(event,force=True)])
    delta = event.delta
    if delta > 0:
        text.font['size'] += 3
    elif delta < 0:
        text.font['size'] -= 3
    updatepack()
    return 'break'
def mousewheel(event):
    window.after(1,lambda:highlight(event))
    delta = event.delta
    if delta > 0:
        text.yview_scroll(-1,'units')
    elif delta < 0:
        text.yview_scroll(1,'units')
text.bind('<ButtonPress-1>',lambda _:complist.place_forget())
text.bind('<Key>',typing)
text.bind('<BackSpace>',deltext)
text.bind('<Return>',rettext)
text.bind('<Tab>',tabtext)
text.bind('<Shift-Tab>',untabtext)
text.bind('<Control-slash>',comment)
text.bind('<Control-Z>',undo)
text.bind('<Control-z>',undo)
text.bind('<Control-Shift-Z>',redo)
text.bind('<Control-Shift-z>',redo)
text.bind('<Control-X>',cut)
text.bind('<Control-x>',cut)
text.bind('<Control-C>',copy)
text.bind('<Control-c>',copy)
text.bind('<Control-V>',paste)
text.bind('<Control-v>',paste)
text.bind('<Delete>',delete)
text.bind('<Control-D>','break')
text.bind('<Control-d>','break')
text.bind('<Control-A>',lambda _:text.tag_add('sel','1.0','end'))
text.bind('<Control-a>',lambda _:text.tag_add('sel','1.0','end'))
text.bind('<Control-MouseWheel>',resize)
text.bind('<ButtonPress-3>',lambda event:editmenu.post(event.x_root,event.y_root))
window.bind('<F9>',compiles)
window.bind('<F10>',run)
window.bind('<F11>',compilerun)
window.bind('<F5>',compilerun)
window.bind('<F3>',setproblem)
window.bind('<F4>',p.judge)
window.bind('<Control-N>',new)
window.bind('<Control-n>',new)
window.bind('<Control-O>',openfile)
window.bind('<Control-o>',openfile)
window.bind('<Control-S>',savefile)
window.bind('<Control-s>',savefile)
window.bind('<Control-Shift-S>',saveasfile)
window.bind('<Control-Shift-s>',saveasfile)
window.bind('<Alt-Key-1>',__insertconsoletemplate)
window.bind('<Alt-Key-2>',__insertwindowstemplate)
text.bind('<B2-Motion>','break')
linetext.bind('<B2-Motion>','break')
text.bind('<F1>',show_help)
text.bind('<<Selection>>',updatescroll)
text.bind_all('<MouseWheel>',mousewheel)
window.bind('<Configure>',lambda event:updatescroll(event,force=True))
update(force=True)
Thread(target=update_thread,daemon=True).start()
text.pack(fill='both',expand=True)
window.update()
windll.user32.SetClassLongPtrW(windll.user32.GetParent(window.winfo_id()),-14,0)
windll.user32.SetClassLongPtrW(windll.user32.GetParent(window.winfo_id()),-34,0)
windll.user32.SetWindowLongPtrW(window.winfo_id(),-20,0)
windll.user32.SetWindowLongPtrW(windll.user32.GetParent(window.winfo_id()),-20,65793)
menubar.update()
menubar.bind('<B1-Motion>',lambda _:windll.user32.ReleaseCapture(),windll.user32.SendMessageW(windll.user32.GetParent(window.winfo_id()),274,61458,0))
window.protocol('WM_DELETE_WINDOW',exits)
window.withdraw()
if len(argv) >= 2:
    if exists(argv[1]):
        try:
            with open(argv[1],'r',encoding=encode) as f:
                text.delete('1.0','end')
                text.insert('end',f.read().rstrip('\n'))
        except:
            _exit(windll.user32.MessageBoxW(0,f'加载失败。\n{type(e).__name__}: {e}',window.title(),16))
        file = argv[1]
        window.title(file+' - '+window.appname)
    else:
        windll.user32.MessageBoxW(0,f'文件无法打开。文件未找到。',window.title(),16)
    highlight()
    updatescroll()
window.state('iconic')
window.state('normal')
window.deiconify()
window.focus_force()
text.focus_set()
window.mainloop()
