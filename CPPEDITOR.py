from _tkinter import TclError
from tkinter import Tk,Entry,Toplevel,Label,Button,Checkbutton,Frame,Menubutton,Text,Listbox,Menu,BooleanVar,Scrollbar as tkScrollbar
from tkinter import ttk,font
from tkinter.filedialog import askopenfilename,asksaveasfilename
from tkinter.scrolledtext import ScrolledText as Stext
from ctypes import WinError, windll,c_uint64,WINFUNCTYPE,c_int,c_long,create_unicode_buffer,sizeof,byref,wintypes
from re import finditer,MULTILINE
import re as _re
from os import _exit,listdir,startfile,kill,remove as delfile,walk,getenv,mkdir,makedirs
from os.path import dirname,join,exists,normpath,expandvars
from threading import Thread
from winreg import QueryValueEx,OpenKey
from subprocess import run as runcmd,Popen,PIPE,STDOUT,CREATE_NEW_CONSOLE,TimeoutExpired
from sys import argv
from random import randint
from tempfile import gettempdir
from time import sleep,time
from winsound import MessageBeep
from pathlib import Path
from datetime import datetime
isdark = False
windll.user32.CallNextHookEx.argtypes = (wintypes.HHOOK,c_int,wintypes.WPARAM,wintypes.LPARAM)
window = Tk()
window.withdraw()
window.showcomp = False
window.showproblem = False
window.appname = 'C++ Editor'
window.namespace = 'cppeditor'
window.version = '26.2.1'
windll.shell32.SetCurrentProcessExplicitAppUserModelID(window.namespace)
window.gccdir = '{DefaultDirectory}'
window.addcmd = '-static'
window.compargv = ''
window.title(window.appname)
window.configure(bg='#171717' if isdark else '#F0F0F0')
window.geometry('650x420')
def log(message: str, level: str = 'INFO'):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {level}: {message}'
    try:
        print(line)
    except Exception:
        pass
    try:
        log_path = get_log_path()
        makedirs(dirname(log_path), exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as lf:
            lf.write(line + '\n')
    except Exception:
        pass
def get_config_path():
    path = join(getenv("localappdata"), f'{window.namespace}/data.txt')
    log(path)
    return path
def get_log_path():
    try:
        return join(getenv("localappdata"), f'{window.namespace}/log.txt')
    except Exception:
        return 'log.txt'
def save_config():
    path = get_config_path()
    try:
        makedirs(join(getenv("localappdata"), window.namespace),exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(str(window.gccdir).replace('\r','') + '\n')
            f.write(str(window.addcmd).replace('\r','') + '\n')
    except Exception as e:
        windll.user32.MessageBoxW(0,f"配置文件保存失败！\n{type(e).__name__}: {e}",0,16)
        log(f'Failed to save config: {type(e).__name__}: {e}', level='ERROR')

def load_config():
    global includesdir
    path = get_config_path()
    try:
        if exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                lines = [l.rstrip('\n') for l in f.readlines()]
            if len(lines) >= 1 and lines[0] != '':
                window.gccdir = lines[0]
                globals()['includesdir'] = [dirname(dirname(window.gccdir)),]
                log(f'includesdir={includesdir}')
            if len(lines) >= 2 and lines[1] != '':
                window.addcmd = lines[1]
    except Exception as e:
        windll.user32.MessageBoxW(0,f"配置文件读取失败！\n{type(e).__name__}: {e}",0,16)
        log(f'Failed to load config: {type(e).__name__}: {e}', level='ERROR')
        # do not exit; continue with defaults

# load persisted config at startup
load_config()
log(includesdir)
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
includesdir = [r'MinGW64']
# Precompile commonly used patterns for faster highlighting
COMPILED_PATTERNS = [
    (_re.compile(r'#.*$', _re.MULTILINE), 'red'),
    (_re.compile(r"//.*$|/\*[\s\S]*?\*/", _re.MULTILINE), 'grey'),
    (_re.compile(r"\b(try|catch|switch|typedef|if|else|case|default|public|protected|private|for|do|while|return|int|break|continue|char|float|double|bool|void|auto|short|long|signed|static|unsigned)\b"), 'yellow'),
    (_re.compile(r"\b(class|struct|using|delete|typename|sizeof|const|volatile|operator|namespace)\b"), 'blue'),
    (_re.compile(r"\b(new|true|false|NULL)\b"), 'orange'),
    (_re.compile(r"\b\d+\b"), 'purple'),
    (_re.compile(r'(".*?(?:\"|$)|".*")|(\'.*?(?:\'|$)|\'.*\')', _re.MULTILINE), 'green'),
]
INCLUDE_RE = _re.compile(r'#include\s*(?:"([^"]+)"|<([^>]+)>)')
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
    else:
        return -1
    highlight()
    updatescroll()
    return road
def issavefile():
    updatescroll()
    if file == None and text.get('1.0','end').replace(' ','').replace('\n','') == '':return 0
    ans = windll.user32.MessageBoxW(window.winfo_id(),'是否保存？',window.title(),35)
    if ans == 6:
        return savefile()
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
        return saveasfile()
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
using namespace std;

int main() {
'''+'    '+'''
    return 0;
}''')
    text.mark_set('insert','5.4')
    window.after(1,lambda:[highlight(),updatescroll(force=False)])
tempmenu.add_command(label='插入经典控制台头文件模板    ',accelerator='Alt+1',command=__insertconsoletemplate)
def compiles(self=None,filec=None,temp=False):
    global file,compiling
    log(f'Starting compilation. filec={filec} temp={temp} file={file}', 'INFO')
    filek = file
    updatescroll()
    if filec:
        filek = filec
    if filek:
        if not temp:
            if savefile() == -1:
                return -1
        if exists(filek.rstrip('.cpp')+'.exe'):delfile(filek.rstrip('.cpp')+'.exe')
        compiling = True
        if window.gccdir == '{DefaultDirectory}':
            gccdir = join(dirname(argv[0]),'mingw64\\bin\\g++.exe')
        else:
            gccdir = window.gccdir
        try:
            cmd = [gccdir,filek.replace('/','\\'),'-o',filek.replace('/','\\').rstrip('.cpp')+'.exe',window.addcmd]
            log(f'Invoke compiler: {cmd}', 'INFO')
            process = Popen(cmd,stdout=PIPE,stderr=STDOUT,text=True,bufsize=1,universal_newlines=True,encoding='utf-8',errors='ignore')
        except Exception:
            try:
                cmd = [gccdir,filek.replace('/','\\'),'-o',filek.replace('/','\\').rstrip('.cpp')+'.exe',window.addcmd]
                log(f'Invoke compiler with cwd dirname(gccdir): {cmd}', 'INFO')
                process = Popen(cmd,cwd=dirname(gccdir),stdout=PIPE,stderr=STDOUT,text=True,bufsize=1,universal_newlines=True,encoding='utf-8',errors='ignore')
            except Exception:
                log('Failed to start compiler process', 'ERROR')
                downloadgcc()
                return 1
        # collect entries as tuples (type, line) to display reliably later
        entries = []
        ew = 0
        out = ''
        while process.poll() is None:
            try:
                line = process.stdout.readline()
            except UnicodeDecodeError:
                line = ''
            if line:
                out += line
                l = line.strip()
                # classify compiler output lines containing error/warning
                if 'error:' in l or 'ld.exe:' in l:
                    entries.append(('error', l))
                    ew += 1
                elif 'warning:' in l:
                    entries.append(('warning', l))
                    ew += 1
                if ew >= 50:
                    process.terminate()
                    process.kill()
                    break
                log(f'compiler output: {line.rstrip()}', 'INFO')
        try:
            rem = process.stdout.read()
            if rem:
                out += rem
        except Exception:
            pass
        # parse any remaining output for errors/warnings
        try:
            for ln in out.splitlines():
                l = ln.strip()
                if not l:
                    continue
                if ('error:' in l or 'ld.exe:' in l) and not any(l == e[1] for e in entries):
                    entries.append(('error', l))
                elif 'warning:' in l and not any(l == e[1] for e in entries):
                    entries.append(('warning', l))
        except Exception:
            pass
        compiling = False
        # If there are warnings only, prompt whether to continue
        warnings_only = [t for t in entries if t[0] == 'warning']
        if warnings_only:
            warn_text = '\n'.join([w[1] for w in warnings_only])
            MessageBeep(48);
#             if windll.user32.MessageBoxW(window.winfo_id(),f'{warn_text}\n\n是否继续运行？',f'警告',49) == 2:
#                 if entries:
#                     show_error_pane(entries)
#                 return 2
        exe_path = filek.replace('/','\\').rstrip('.cpp')+'.exe'
        has_error = any(t[0] == 'error' for t in entries)
        if has_error or not exists(exe_path):
            # prefer to show error lines if available
            if has_error:
                msg = '\n'.join([t[1] for t in entries if t[0] == 'error'])
            else:
                msg = out if out else '编译失败，未生成可执行文件。'
            log(f'Compilation failed: {msg}', 'ERROR')
            # show error pane with collected entries
            if entries:
                show_error_pane(entries)
            MessageBeep(16);
#            return windll.user32.MessageBoxW(window.winfo_id(),msg,'错误',16)
            return;
        else:
            log(f'Compilation succeeded, exe at {exe_path}', 'INFO')
            # show warnings (non-blocking) in pane if present
            if entries:
                show_error_pane(entries)
    else:
        if issavefile() in [-1,0]:
            return -1
        else:
            compiles(self)
def execute(file,temp=False,args=[]):
    updatescroll()
    if (not exists(file.rstrip('.cpp')+'.exe')):
        return 1
    tmp = window.state()
    window.state('iconic')
    currdir = join(dirname(__file__),'ConsolePauser.exe')
    try:
        log(f'Executing project', 'INFO')
        runcmd([currdir,file.rstrip('.cpp')+'.exe']+args,creationflags=CREATE_NEW_CONSOLE)
        if temp:
            for i in range(3):
                try:
                    if exists(file.rstrip('.cpp')+'.exe'):
                        delfile(file.rstrip('.cpp')+'.exe')
                        break
                except PermissionError:
                    sleep(0.1)
    except:
        log('Execution failed', 'ERROR')
        return 1;
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
                compiles(self,file)
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
    compiles(filec=filet,temp=True);
    try:
        delfile(filet)
        Thread(target=execute,args=(filet,True,args),daemon=False).start()
    except OSError:
        pass
def compilerun(self=None):
    if self:
        if not file:        
            return compilerunintemp()
    if compiles(filec=file) != -1:
        run()
def select(toplevel):
    global includesdir
    file = askopenfilename(parent=toplevel,title='选择 g++.exe 的路径（不是 gcc.exe）',defaultextension='.exe',filetypes=[('Executable file','.exe'),])
    if not file:
        return
    if 'g++.exe' in file:
        toplevel.gccdir.delete(0,'end')
        toplevel.gccdir.insert('end',file.replace('/','\\'))
        window.gccdir = toplevel.gccdir.get()
        includesdir = [dirname(dirname(window.gccdir)),]
        log(f'Set gccdir to {window.gccdir}; includesdir={includesdir}', 'INFO')
    else:
        windll.user32.MessageBoxW(toplevel.winfo_id(),'选择的文件不是有效文件，文件名必须为 g++.exe。','错误',16)
def revert(toplevel):
    global includesdir
    toplevel.gccdir.delete(0,'end'),
    toplevel.gccdir.insert('end','{DefaultDirectory}'),
    window.gccdir = toplevel.gccdir.get()
    includesdir = [r"MinGW64"]
def revert2(toplevel):
    toplevel.addcmd.delete(0,'end'),
    toplevel.addcmd.insert('end','-static'),
    window.addcmd = toplevel.addcmd.get()
def envconfig(self=None):
    def saveandexit(toplevel):
        window.gccdir = toplevel.gccdir.get()
        window.addcmd = toplevel.addcmd.get()
        save_config()
        window.attributes('-disabled',False)
        toplevel.destroy()
        window.focus_force()
    toplevel = Toplevel(window)
    toplevel.withdraw()
    toplevel.transient(window)
    toplevel.resizable(0,0)
    toplevel.geometry(f'500x360+200+200')
    toplevel.title(f'环境配置 - {window.appname}')
    toplevel.configure(bg='#171717' if isdark else '#F0F0F0')
    Label(toplevel,bg=toplevel['bg'],fg='#FFFFFF' if isdark else '#000000',text='环境配置',font=('Microsoft Yahei UI',17)).pack(pady=2)
    Frame(toplevel,bg=toplevel['bg'],width=0,height=0).pack(side='bottom',pady=4)
    Button(toplevel,text='保存并退出',bg='#202020' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000',activebackground='#602020' if isdark else '#FFFFFF',activeforeground='#FFFFFF' if isdark else '#000000',command=lambda:saveandexit(toplevel),font=('Microsoft Yahei UI',12)).place(x=387,y=314,width=98,height=32)
    toplevel.frame = Frame(toplevel,bg=toplevel['bg'])
    Label(toplevel.frame,bg=toplevel['bg'],fg='#FFFFFF' if isdark else '#000000',text='g++.exe 的目录',font=('Microsoft Yahei UI',14)).pack(padx=2,anchor='w',side='left')
    Button(toplevel.frame,text='选择',bg='#202020' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000',activebackground='#602020' if isdark else '#FFFFFF',activeforeground='#FFFFFF' if isdark else '#000000',command=lambda:select(toplevel),font=('Microsoft Yahei UI',9),width=5).pack(side='right',expand=True)
    Button(toplevel.frame,text='默认',bg='#202020' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000',activebackground='#602020' if isdark else '#FFFFFF',activeforeground='#FFFFFF' if isdark else '#000000',command=lambda:revert(toplevel),font=('Microsoft Yahei UI',9),width=5).pack(side='right',expand=True)
    toplevel.gccdir = Entry(toplevel.frame,width=9999,bd=1,bg='#171717' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000',insertbackground='#FFFFFF' if isdark else '#000000',font=('Microsoft Yahei UI',13))
    toplevel.gccdir.insert('end',window.gccdir)
    toplevel.gccdir.pack(side='right',fill='x',padx=2,expand=True)
    toplevel.frame.pack()
    
    toplevel.frame = Frame(toplevel,bg=toplevel['bg'])
    Label(toplevel.frame,bg=toplevel['bg'],fg='#FFFFFF' if isdark else '#000000',text='编译追加命令(在编译命令之后)',font=('Microsoft Yahei UI',14)).pack(padx=2,anchor='w',side='left')
    Button(toplevel.frame,text='默认',bg='#202020' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000',activebackground='#602020' if isdark else '#FFFFFF',activeforeground='#FFFFFF' if isdark else '#000000',command=lambda:revert2(toplevel),font=('Microsoft Yahei UI',9),width=5).pack(side='right',expand=True)
    toplevel.addcmd = Entry(toplevel.frame,width=9999,bd=1,bg='#171717' if isdark else '#F0F0F0',fg='#FFFFFF' if isdark else '#000000',insertbackground='#FFFFFF' if isdark else '#000000',font=('Microsoft Yahei UI',13))
    toplevel.addcmd.insert('end',window.addcmd)
    toplevel.addcmd.pack(side='right',fill='x',padx=2,expand=True)
    toplevel.frame.pack()
    toplevel.update()
    windll.dwmapi.DwmSetWindowAttribute(windll.user32.GetParent(toplevel.winfo_id()),20,byref(c_int(isdark)),sizeof(c_int))
    windll.dwmapi.DwmSetWindowAttribute(windll.user32.GetParent(toplevel.winfo_id()),35,byref(c_int(0x171717 if isdark else 0xF0F0F0)),sizeof(c_int))
    windll.user32.SendMessageW(windll.user32.GetParent(toplevel.winfo_id()),274,61728,0)
    window.attributes('-disabled',True)
    toplevel.bind('<Escape>',lambda _:[window.attributes('-disabled',False),toplevel.destroy(),window.focus_force()])
    toplevel.protocol('WM_DELETE_WINDOW',lambda:[window.attributes('-disabled',False),toplevel.destroy(),window.focus_force()])
    toplevel.focus_force()
    window.wait_window(toplevel)

compmenu = Menu(window,tearoff=False,bg='#202020' if isdark else '#FFFFFF',fg='#FFFFFF' if isdark else '#000000')
compmenu.add_command(label='编译(C)    ',underline=3,accelerator='F9',command=compiles)
compmenu.add_command(label='运行(R)    ',underline=3,accelerator='F10',command=run)
compmenu.add_command(label='编译并运行(E)    ',underline=6,accelerator='F11, F5',command=compilerun)
compmenu.add_command(label='在临时目录编译并运行(T)    ',underline=11,accelerator='    ',command=compilerunintemp)
compmenu.add_separator()
compmenu.add_command(label='环境配置(O)    ',underline=5,accelerator='    ',command=envconfig)
def run_process_with_input(command,input_text,timeout=None):
    try:
        if isinstance(command, str):
            command = shlex.split(command)
        stdout, stderr = proc.communicate(input=input_text, timeout=timeout)
        return proc.returncode,stdout,stderr
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
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
        except:
            windll.user32.MessageBoxW(window.winfo_id(),'Compile Error','Error',16)
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
        compiles(filec=filet,temp=True)
        try:
            delfile(filet)
            Thread(target=self.execute,args=(filet,True),daemon=False).start()
        except OSError:
            pass
p = Problem(window)

# --- Error preview pane (shows compiler errors/warnings) ---
error_pane = Frame(window, bg='#171717', bd=1)
error_pane.visible = False
error_pane.header = Frame(error_pane, bg='#171717')
error_pane.title = Label(error_pane.header, text='编译结果', bg='#171717', fg='#FFFFFF', font=('Microsoft Yahei UI',11))
error_pane.title.pack(side='left', padx=6)
error_pane.closebtn = Button(error_pane.header, text='关闭(ESC)', command=lambda: hide_error_pane(), bd=0, font=('Microsoft Yahei UI',11))
error_pane.closebtn.pack(side='right', padx=6)
error_pane.header.pack(fill='x')
error_pane.text = Text(error_pane, height=6, bg='#2D2D2D', fg='#FFFFFF', bd=0, highlightthickness=0, wrap='word',font=(text.font['family'],10))
error_pane.vbar = Scrollbar(error_pane, orient='vertical')
error_pane.vbar.text = error_pane.text
error_pane.vbar.configure(command=error_pane.text.yview)
error_pane.text.configure(yscrollcommand=error_pane.vbar.set)
error_pane.vbar.pack(side='right', fill='y')
error_pane.text.pack(fill='both', expand=True, padx=4, pady=4)

def show_error_pane(entries):
    """entries: list of (type, text) where type is 'error' or 'warning'"""
    try:
        # populate text widget with colored tags per line
        error_pane.text.configure(state='normal')
        error_pane.text.delete('1.0', 'end')
        for typ, line in entries:
            tag = 'error' if typ == 'error' else 'warning'
            error_pane.text.insert('end', line + '\n', tag)
        # configure tags (ensure created)
        try:
            error_pane.text.tag_configure('error', background='#8B0000', foreground='#FFFFFF')
            error_pane.text.tag_configure('warning', background='#FFCC00', foreground='#000000')
        except Exception:
            pass
        error_pane.text.configure(state='disabled')
        error_pane.visible = True
        # pack and focus so Esc can close it
        try:
            error_pane.pack(side='bottom', fill='x')
        except Exception:
            pass
        try:
            # bind Escape to hide when pane is visible
            window.bind('<Escape>', lambda e: hide_error_pane())
        except Exception:
            pass
        updatepack()
    except Exception:
        pass

def hide_error_pane():
    try:
        error_pane.visible = False
        try:
            error_pane.pack_forget()
        except Exception:
            pass
        try:
            # remove Escape binding if present
            window.unbind('<Escape>')
        except Exception:
            pass
        updatepack()
    except Exception:
        pass

def updatepack(self=None):
    p.problem.pack_forget()
    text.pack_forget()
    menubar.pack_forget()
    vsbar.pack_forget()
    bottombox.pack_forget()
    linetext.pack_forget()
    findbox.pack_forget()
    complist.configure(font=('Microsoft Yahei UI',text.font['size']-6))
    # ensure menubar is packed once at the top
    menubar.pack(side='top',fill='x',expand=True)
    # pack problem pane (right) first if visible
    if window.showproblem:
        p.problem.pack(side='right',fill='y',expand=True)
    # show or hide findbox under menubar
    if findbox.visible:
        findbox.pack(side='top', fill='x')
    else:
        findbox.pack_forget()
    # main editor area
    vsbar.pack(side='right',fill='y',expand=True)
    linetext.pack(side='left',fill='y',expand=True)
    text.pack(fill='both',expand=True)
    # error pane sits above the bottom controls (bottombox)
    if error_pane.visible:
        error_pane.pack(side='bottom', fill='x')
    bottombox.pack(side='bottom',fill='x',expand=True)
    # ensure findbox stays immediately under menubar when visible
# --- Find / Replace bar (hidden by default) ---
# Use a unified dark background for the find/replace bar so its appearance stays consistent
findbox = Frame(window, bg='#171717', bd=1)
findbox.visible = False
# Minimal controls: find entry, match-case toggle, prev/next, optional replace entry and replace actions
findbox.find_entry = Entry(findbox, width=0, bd=1, font=('Consolas', 12), bg='#171717', fg='#FFFFFF', insertbackground='#FFFFFF')
# Let the find entry take remaining horizontal space so buttons don't squeeze it
findbox.find_entry.pack(side='left', padx=4, pady=4, fill='x', expand=True)
def _find_entry_return(event):
    replace_mode = hasattr(findbox, 'replace_entry') and getattr(findbox.replace_entry, 'winfo_ismapped', lambda: False)()
    do_find(backwards=False, replace_current=replace_mode)
    return 'break'

def _find_entry_shift_return(event):
    replace_mode = hasattr(findbox, 'replace_entry') and getattr(findbox.replace_entry, 'winfo_ismapped', lambda: False)()
    do_find(backwards=True, replace_current=replace_mode)
    return 'break'

findbox.find_entry.bind('<Return>', _find_entry_return)
findbox.find_entry.bind('<Shift-Return>', _find_entry_shift_return)
findbox.match_var = BooleanVar(value=False)
# Use a Checkbutton for match-case with theme-aware styling
findbox.match_cb = Checkbutton(findbox, text='匹配大小写', variable=findbox.match_var, onvalue=True, offvalue=False, width=8, bd=0, bg='#171717', fg='#FFFFFF', selectcolor='#171717',activebackground='#171717', activeforeground='#FFFFFF')
findbox.match_cb.pack(side='left', padx=4)
findbox.find_prev_btn = Button(findbox, text='Prev', command=lambda: do_find(backwards=True, replace_current=(hasattr(findbox, 'replace_entry') and getattr(findbox.replace_entry, 'winfo_ismapped', lambda: False)())), bd=0)
findbox.find_prev_btn.pack(side='left', padx=2)
findbox.find_next_btn = Button(findbox, text='Next', command=lambda: do_find(backwards=False, replace_current=(hasattr(findbox, 'replace_entry') and getattr(findbox.replace_entry, 'winfo_ismapped', lambda: False)())), bd=0)
findbox.find_next_btn.pack(side='left', padx=2)
findbox.close_btn = Button(findbox, text='Close', command=lambda: hide_findbox(), bd=0)
findbox.close_btn.pack(side='left', padx=4)
# replace controls created lazily when needed
def _ensure_replace_controls():
    if not hasattr(findbox, 'replace_entry'):
        btn_bg = '#171717' if isdark else '#F0F0F0'
        btn_fg = '#FFFFFF' if isdark else '#000000'
        active_bg = '#602020' if isdark else '#FFFFFF'
        active_fg = '#FFFFFF' if isdark else '#000000'
        findbox.replace_entry = Entry(findbox, width=12, background=btn_bg,foreground=btn_fg,insertbackground=active_fg,bd=1, font=('Consolas', 12))
        # Theme-aware buttons for replace actions
        findbox.replace_btn = Button(findbox, text='Replace', command=lambda: do_replace(), bd=0)
        findbox.replace_all_btn = Button(findbox, text='Replace All', command=lambda: replace_all(), bd=0)
        # pack replace controls to the left of close button
        # Pack replace controls to the right of the expanding find entry so they have fixed space
        findbox.replace_entry.pack(side='left', padx=4, pady=4)
        findbox.replace_btn.pack(side='left', padx=2)
        findbox.replace_all_btn.pack(side='left', padx=2)
        # bind Enter / Shift+Enter on replace entry to replace+find
        def _replace_entry_return(event):
            # perform replace on current selection if it matches, then find next
            do_find(backwards=False, replace_current=True)
            return 'break'
        def _replace_entry_shift_return(event):
            do_find(backwards=True, replace_current=True)
            return 'break'
        update(force=True);
        findbox.replace_entry.bind('<Return>', _replace_entry_return)
        findbox.replace_entry.bind('<Shift-Return>', _replace_entry_shift_return)
show_replace_old = True
def show_findbox(show_replace=False):
    try:
        # show findbox and re-layout main window so findbox sits under menubar
        findbox.visible = not findbox.visible
        if (not findbox.visible):
            text.focus_set()
        # if switching out of replace mode, hide all replace controls
        if not show_replace and hasattr(findbox, 'replace_entry'):
            findbox.replace_entry.pack_forget()
            findbox.replace_btn.pack_forget()
            findbox.replace_all_btn.pack_forget()
        # ensure replace controls if requested and show them
        if show_replace:
            try:
                _ensure_replace_controls()
            except Exception:
                pass
            try:
                # pack them (they may already be packed inside _ensure_replace_controls)
                # ensure replace entry uses unified background
                try:
                    findbox.replace_entry.configure(bg='#171717', fg='#FFFFFF', insertbackground='#FFFFFF')
                except Exception:
                    pass
                findbox.replace_entry.pack(side='left', padx=4, pady=4)
                findbox.replace_btn.pack(side='left', padx=2)
                findbox.replace_all_btn.pack(side='left', padx=2)
                findbox.close_btn.pack(side='left', padx=4)
            except Exception:
                pass
        # rebuild layout placing findbox under menubar
        try:
            updatepack()
        except Exception:
            pass
        findbox.find_entry.focus_set()
    except Exception:
        pass
    return 'break'
def hide_findbox():
    try:
        findbox.visible = False
        # rebuild layout without findbox
        try:
            updatepack()
        except Exception:
            try:
                findbox.pack_forget()
            except Exception:
                pass
        window.update_idletasks()
    except Exception:
        pass
    text.focus_force()
    text.focus_set()
    return 'break'
def _clear_found():
    try:
        text.tag_remove('found', '1.0', 'end')
    except Exception:
        pass

def do_find(backwards=False, replace_current=False):
    """
    Find next/previous occurrence. If replace_current is True and replace controls exist,
    replace the current selection before moving to next match.
    """
    log(f"invoked do_find back={backwards} replace={replace_current}","INFO")
    _clear_found()
    pattern = findbox.find_entry.get()
    if not pattern:
        return

    # If requested, replace current selection first
    if replace_current and hasattr(findbox, 'replace_entry'):
        try:
            sel_start = text.index('sel.first')
            sel_end = text.index('sel.last')
            repl = findbox.replace_entry.get()
            text.delete(sel_start, sel_end)
            text.insert(sel_start, repl)
            # move insert after inserted text
            text.mark_set('insert', f"{sel_start}+{len(repl)}c")
            _clear_found()
        except Exception:
            # nothing to replace
            pass

    start_index = text.index('insert')
    nocase = not findbox.match_var.get()
    try:
        if backwards:
            res = text.search(pattern, start_index, stopindex='1.0', backwards=True, nocase=nocase)
        else:
            res = text.search(pattern, start_index, stopindex='end', nocase=nocase)
    except Exception:
        res = ''
    if not res:
        # try from top / bottom
        try:
            if backwards:
                res = text.search(pattern, 'end', stopindex='1.0', backwards=True, nocase=nocase)
            else:
                res = text.search(pattern, '1.0', stopindex='end', nocase=nocase)
        except Exception:
            res = ''
    if res:
        end_index = f"{res}+{len(pattern)}c"
        try:
            text.tag_add('found', res, end_index)
            text.mark_set('insert', end_index)
            text.see(res)
            text.tag_remove('sel', '1.0', 'end')
            text.tag_add('sel', res, end_index)
        except Exception:
            pass

def do_replace():
    try:
        sel_start = text.index('sel.first')
        sel_end = text.index('sel.last')
    except Exception:
        # no selection, find next
        do_find(backwards=False)
        return
    repl = findbox.replace_entry.get()
    try:
        text.delete(sel_start, sel_end)
        text.insert(sel_start, repl)
        _clear_found()
        text.mark_set('insert', f"{sel_start}+{len(repl)}c")
        highlight()
    except Exception:
        pass

def replace_all():
    pattern = findbox.find_entry.get()
    if not pattern:
        return
    repl = findbox.replace_entry.get()
    start = '1.0'
    nocase = not findbox.match_var.get()
    count = 0
    while True:
        idx = text.search(pattern, start, stopindex='end', nocase=nocase)
        if not idx:
            break
        end = f"{idx}+{len(pattern)}c"
        try:
            text.delete(idx, end)
            text.insert(idx, repl)
            start = f"{idx}+{len(repl)}c"
            count += 1
        except Exception:
            break
    highlight()
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
    if windll.user32.MessageBoxExW(window.winfo_id(),f'''{window.appname} v{window.version}。
野生坤坤没头像制作。
THIS SOFTWARE BELONGS TO YESOFTWARE.
http://www.yeskunkun.cn/
一个追求界面极致精简的编辑器，适合日常刷题和写写小项目。
没有任何诋毁其它编辑器的意思。如果有建议可以视频下留言或私信我。

鸣谢名单：
bilibili@bzimage - 让我给编辑器起名字。
bilibili@羊行古、bilibili@矢与珏 - 增加 GCC 参数设置入口。

最新更新：
增加头文件判断功能、参数设置入口。
计划更新：
OJ功能增加 Markdown支持。''',f'关于',65,0x00000904) == 1:
        startfile('http://www.yeskunkun.cn/')
    windll.user32.UnhookWindowsHookEx(h_hook)
def downloadgcc(self=None):
    windll.user32.MessageBoxW(window.winfo_id(),"没有找到 MinGW 安装目录，请手动指定或者在当前目录下放置 MinGW 文件夹。",0,16)
    return
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
    windll.dwmapi.DwmSetWindowAttribute(windll.user32.GetParent(toplevel.winfo_id()),20,byref(c_int(isdark)),sizeof(c_int))
    windll.dwmapi.DwmSetWindowAttribute(windll.user32.GetParent(toplevel.winfo_id()),35,byref(c_int(0x171717 if isdark else 0xF0F0F0)),sizeof(c_int))
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
    try:
        top_index = text.index('@0,0')
        bottom_index = text.index(f'@0,{max(1,text.winfo_height())}')
        top_line = int(top_index.split('.')[0])
        bottom_line = int(bottom_index.split('.')[0])
        # include one extra line to ensure partial bottom line is covered
        return (f'{top_line}.0', f'{bottom_line+1}.0')
    except Exception:
        return ('1.0','end-1c')
import os
def search_file_recursive(root_dir: str, target_filename: str) -> bool:
    # 遍历当前目录所有文件/子目录
    # Use os.walk (iterative) instead of os.scandir to avoid issues
    # Skip common large/system dirs to speed up search
    try:
        for root, dirs, files in walk(root_dir, topdown=True):
            # prune dirs we don't want to traverse
            dirs[:] = [d for d in dirs if d.lower() not in ('bin', 'libexec', 'share')]
            for fn in files:
                try:
                    if fn.lower() == target_filename.lower():
                        log(f'Found include {target_filename} at {join(root, fn)}', 'INFO')
                        return True
                except Exception:
                    continue
    except Exception as e:
        log(f'Error during walk: {type(e).__name__}: {e}', 'ERROR')
    return False
import os
def highlight(self=None):
    global text, linetext,includesdir
    try:
        linetext.yview_moveto(text.yview()[0])
    except Exception:
        pass

    vis_start, vis_end = getvisibleline()
    try:
        visible = text.get(vis_start, vis_end)
    except Exception:
        vis_start = '1.0'
        visible = text.get('1.0', 'end-1c')
    for tag in ('red','green','yellow','blue','orange','purple','grey','include_missing'):
        try:
            text.tag_remove(tag, vis_start, vis_end)
        except Exception:
            pass
    for pattern, tag in COMPILED_PATTERNS:
        try:
            for m in pattern.finditer(visible):
                start = f'{vis_start}+{m.start()}c'
                end = f'{vis_start}+{m.end()}c'
                if tag == 'green':
                    # remove conflicting tags within this span
                    for conflicting in ('red','yellow','blue','orange','purple'):
                        try:
                            text.tag_remove(conflicting, start, end)
                        except Exception:
                            pass
                try:
                    text.tag_add(tag, start, end)
                except Exception:
                    pass
        except Exception:
            continue
    try:
        current_line = None
        try:
            current_line = text.index('insert').split('.')[0]
        except Exception:
            current_line = None

        for m in INCLUDE_RE.finditer(visible):
            incname = m.group(1) or m.group(2)
            if not incname:
                continue
            start = f'{vis_start}+{m.start()}c'
            line_no = text.index(start).split('.')[0]
            if current_line is None or line_no != current_line:
                continue
            found = False
            includesdir = [dirname(dirname(window.gccdir)),]
            log(f'Prepared for searching {includesdir}')
            for inc_root in includesdir:
                try:
                    if search_file_recursive(inc_root, incname):
                        found = True
                        break
                except Exception:
                    continue
            if not found:
                try:
                    text.tag_add('include_missing', f'{line_no}.0', f'{line_no}.end')
                except Exception:
                    pass
    except Exception:
        pass
def update(self=None,force=False):
    global isdark
    oisdark = isdark
    try:
        isdark = not QueryValueEx(OpenKey(18446744071562067969,r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize'),'AppsUseLightTheme')[0]
    except FileNotFoundError:
        isdark = False
    if isdark != oisdark or force:
        windll.dwmapi.DwmSetWindowAttribute(windll.user32.GetParent(window.winfo_id()),20,byref(c_int(isdark)),sizeof(c_int))
        windll.dwmapi.DwmSetWindowAttribute(windll.user32.GetParent(window.winfo_id()),35,byref(c_int(0x171717 if isdark else 0xF0F0F0)),sizeof(c_int))
        getspace()
        szgrip.style.configure('TSizegrip',background='#171717' if isdark else '#F0F0F0',borderwidth=0)
        windll.uxtheme.SetWindowTheme(vsbar.winfo_id(),'DarkMode_Explorer' if isdark else 0,0)
        vsbar.menu.configure(background='#171717' if isdark else '#F0F0F0',foreground='#FFFFFF' if isdark else '#000000')
        windll.uxtheme.SetWindowTheme(hsbar.winfo_id(),'DarkMode_Explorer' if isdark else 0,0)
        hsbar.menu.configure(background='#171717' if isdark else '#F0F0F0',foreground='#FFFFFF' if isdark else '#000000')
        error_pane.configure(background='#171717' if isdark else '#F0F0F0')
        error_pane.header.configure(background='#171717' if isdark else '#F0F0F0')
        error_pane.title.configure(background='#171717' if isdark else '#F0F0F0',foreground='#FFFFFF' if isdark else '#000000')
        error_pane.closebtn.configure(background='#171717' if isdark else '#F0F0F0',foreground='#FFFFFF' if isdark else '#000000')
        try:
            # theme error pane scrollbar if present
            windll.uxtheme.SetWindowTheme(error_pane.vbar.winfo_id(),'DarkMode_Explorer' if isdark else 0,0)
            try:
                error_pane.vbar.menu.configure(bg=btn_bg, fg=btn_fg)
            except Exception:
                pass
        except Exception:
            pass
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
        text.tag_configure('include_missing',background='#330000' if isdark else '#FFCCCC',foreground='#FFFFFF')
        text.tag_configure('found',background='#FFFF99',foreground='#000000')
        try:
            text.tag_bind('include_missing','<Enter>',lambda e:show_include_tooltip(e))
            text.tag_bind('include_missing','<Leave>',lambda e:hide_include_tooltip(e))
        except Exception:
            pass
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
        findbox.configure(bg='#171717')
        btn_bg = '#171717' if isdark else '#F0F0F0'
        btn_fg = '#FFFFFF' if isdark else '#000000'
        active_bg = '#602020' if isdark else '#FFFFFF'
        active_fg = '#FFFFFF' if isdark else '#000000'
        findbox.configure(background=btn_bg)
        for name in ('find_entry','replace_entry','match_cb','find_prev_btn','find_next_btn','close_btn','replace_btn','replace_all_btn'):
            try:
                if hasattr(findbox, name):
                    w = getattr(findbox, name)
                    # Entries need insertbackground
                    if isinstance(w, Entry):
                        # use unified dark background for entries in the findbar
                        w.configure(background=btn_bg, foreground=btn_fg, insertbackground=active_fg)
                    else:
                        try:
                            w.configure(background=btn_bg, foreground=btn_fg, activebackground=active_bg, activeforeground=active_fg)
                        except Exception:
                            try:
                                w.configure(background=btn_bg, foreground=btn_fg)
                            except Exception:
                                pass
            except Exception:
                pass
    updatescroll()
def update_thread():
    update()
    window.after(2000,update_thread)

# Tooltip for include missing
_inc_tip = None
def show_include_tooltip(event):
    global _inc_tip
    try:
        # compute mouse index and get corresponding line text
        index = text.index(f"@{event.x},{event.y}")
        line = index.split('.')[0]
        line_text = text.get(f'{line}.0',f'{line}.end')
        m = finditer(r'#include\s*(?:"([^"]+)"|<([^>]+)>)', line_text)
        incname = None
        for mm in m:
            incname = mm.group(1) or mm.group(2)
            break
        if not incname:
            return
        if _inc_tip:
            _inc_tip.destroy()
        # create Toplevel tooltip
        _inc_tip = Toplevel(window)
        _inc_tip.wm_overrideredirect(True)
        _inc_tip.configure(bg='#330000' if isdark else '#FFFFE0',cursor='ibeam')
        lab = Label(_inc_tip,text=f'包含文件未找到: {incname}',bg=_inc_tip['bg'],fg='#FFFFFF' if isdark else '#000000',font=('Microsoft Yahei UI',10))
        lab.pack()
        x = window.winfo_rootx()+event.x
        y = window.winfo_rooty()+event.y+20
        _inc_tip.wm_geometry(f'+{x}+{y}')
    except Exception:
        pass

def hide_include_tooltip(event):
    global _inc_tip
    try:
        if _inc_tip:
            _inc_tip.destroy()
            _inc_tip = None
    except Exception:
        _inc_tip = None
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
                    if findbox.visible:
                        y += findbox.winfo_reqheight()
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
        text.delete('insert','insert-1c')
        text.insert('insert','}')
##        text.mark_set('insert','insert+1c')
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
    # throttle repeated resize events to avoid overly fast scaling that may hide UI
    try:
        now = time()
        if not hasattr(window, '_last_resize') or now - window._last_resize > 0.05:
            window._last_resize = now
            window.after(1,lambda:[highlight(event),updatescroll(event,force=True)])
            delta = event.delta
            # delta for MouseWheel varies; normalize small increments
            if delta > 0:
                text.font['size'] += 1
            elif delta < 0:
                text.font['size'] -= 1
            # enforce sensible bounds
            if text.font['size'] < 8: text.font['size'] = 8
            if text.font['size'] > 60: text.font['size'] = 60
            text.update()
    except Exception:
        pass
    return 'break'
def mousewheel(event):
    window.after(1,lambda:highlight(event))
    delta = event.delta
    if delta > 0:
        text.yview_scroll(-1,'units')
    elif delta < 0:
        text.yview_scroll(1,'units')
text.bind('<ButtonPress-1>',lambda _:complist.place_forget())
def _on_any_key(event):
    try:
        _clear_found()
    except Exception:
        pass
text.bind('<Key>', lambda e: (typing(e), _on_any_key(e))[0])
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
window.bind('<Control-f>', lambda e: show_findbox(False))
window.bind('<Control-F>', lambda e: show_findbox(False))
window.bind('<Control-h>', lambda e: show_findbox(True))
window.bind('<Control-H>', lambda e: show_findbox(True))
text.bind('<Control-h>', lambda e: show_findbox(True))
text.bind('<Control-H>', lambda e: show_findbox(True))
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
window.deiconify()
window.focus_force()
text.focus_set()
window.mainloop()