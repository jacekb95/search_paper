import tkinter as tk
from tkinter import filedialog
import tkinter.messagebox
import tkinter.ttk as tkk
from Levenshtein import ratio
from urllib.error import HTTPError
from urllib.parse import quote_plus, urlencode
from urllib.request import urlopen, Request
import json
import os
import pandas as pd
import re

# global variables
PATH = os.getcwd() + "/"
 
class Win1:
    def __init__(self, master):
        self.master = master
        self.font = ("Arial",11)
        self.window()
       
    def window(self):
        
        # menu with options
        menubar = tk.Menu(self.master)
        menubar.add_command(label="Add directory", command=lambda: save_directory_win())
        menubar.add_command(label="Delete directory", command=lambda: delete_directory_win())
        self.master.config(menu=menubar)
        
        self.master.title("Search Papers")
        
        tk.Label(self.master, text="Directory", font=self.font).grid(row=0,column=0,sticky = tk.W + tk.N)
        self.directory_data()
        
        tk.Label(self.master, text="Doi", font=self.font,).grid(row=1,column=0,sticky= tk.W + tk.N)
        self.doi = tk.Entry(self.master,textvariable=1, width=50)
        self.doi.grid(row=1, columnspan=2, column=1, stick = tk.W)
    
        tk.Label(self.master, text="Title", font=self.font,).grid(row=2,column=0,sticky=tk.W + tk.N)
        self.title = tk.Entry(self.master,textvariable=2, width=50)
        self.title.grid(row=2, columnspan=2, column=1, stick = tk.W)
        self.title.focus()
    
        self.button1 = tk.Button(self.master, text='Search', 
                                 font=self.font,
                                 command=self.find_paper)\
            .grid(row=3, column=1,sticky=tk.W+tk.E, pady=4)
        self.button2 = tk.Button(self.master, 
                                 text='Quit', 
                                 font=self.font, 
                                 command=self.master.destroy)\
            .grid(row=3, column=2, sticky=tk.W+tk.E, pady=4)
        
    def directory_data(self):
        self.directory_data = read_directories()
        self.directory_data['Choose another'] = "x"
        self.directory = tkk.Combobox(self.master, width=47, state='readonly', postcommand=self.updtcblist)
        self.directory['values']= list(self.directory_data.keys())
        self.directory.current(0) 
        self.directory.grid(column=1, columnspan = 2 ,row=0,sticky='w')  
        
    def updtcblist(self):
        self.directory_data = read_directories()
        self.directory_data['Choose another'] = "x"
        self.directory['values'] = list(self.directory_data.keys())
    
    def find_paper(self):
        
        self.out = self.path()
        if self.out == False:
            return
    
        DOI = self.doi.get()
        TITLE = self.title.get()
        if DOI != "" and TITLE != "":
            tkinter.messagebox.showwarning("Warning", "Too much information provided")
            return 
        
        if DOI != "":
            Win2(self.out,DOI,doi=True)
            self.doi.delete(0, tk.END)
        
        if TITLE != "":
            Win2(self.out,TITLE)
            self.title.delete(0, tk.END)
            
    def path(self):
        direc = self.directory.get()
        if direc == "Choose another":
            tmpdir = filedialog.askdirectory(title = "Choose directory to save paper")
            self.out = tmpdir
        else:
            self.out = self.directory_data[direc]               
        return self.out
    
class Win2:
    def __init__(self,out,to_find,doi=False):
        
        self.headers = ['Title', 'Authors', 'Journal', 'Year', 'DOI']
        if doi:
            self.info = self.crossref_query_doi(to_find)
        else:
            self.info = self.crossref_query_title(to_find)
        self.out = out
        if self.info["success"] == False:
            tkinter.messagebox.showwarning("Warning", "Paper has not been found")
        else:
            self.detail = self.info["result"]
            self.top = tk.Toplevel()
            self.build_window()
            
    def build_window(self): 
        
        # initiate
        self.top.title("Paper details") # build window        
        self.display = 0 # display the best match
        self.args_n = 5 # number of arguments 
                
        # lists to save entries and arguments
        self.args = []
        self.entries = []
        
        #assign values do arguments
        for i in range(self.args_n):
            # define argument 
            arg = tk.StringVar()
            arg.set(self.detail[self.headers[i]].iloc[self.display])
            self.args.append(arg)
            
            # create entry with value
            entry = tk.Entry(self.top, font=("Arial",11), width=100,textvariable=arg)
            entry.grid(row=i, column = 1, columnspan=5, sticky = 'w')
            self.entries.append(entry)
            
            #create button 
            tk.Button(self.top, command = lambda entry = entry: copy_to_clip(entry.get()),text= self.headers[i],\
                  font=("Arial",11)).grid(row=i, column = 0, sticky=tk.W+tk.E )
        
        # counter
        self.currecnt_displayed = tk.StringVar()
        self.currecnt_displayed.set(str(self.display+1) + "/" + str(self.detail.shape[0]))
        self.msg61 = tk.Label(self.top, textvariable = self.currecnt_displayed, font=("Arial",11,'bold'))
        self.msg61.grid(row=5, column = 0,sticky = tk.W+tk.E)
        
        # buttons
        tk.Button(self.top, text="\u00ab Back", command= lambda: self.display_new('back'), font=("Arial",11)).grid(row=5, column=1,sticky=tk.W+tk.E, pady=4)
        tk.Button(self.top, text="Next \u00bb", command= lambda: self.display_new('next'), font=("Arial",11)).grid(row=5, column=2,sticky=tk.W+tk.E, pady=4)
        tk.Button(self.top, text="Save \u2193", command=lambda: self.create_bib(), font=("Arial",11)).grid(row=5, column=3,sticky=tk.W+tk.E, pady=4)
        tk.Button(self.top, text="Cancel \u00d7", command=self.close_window, font=("Arial",11)).grid(row=5, column=4,sticky=tk.W+tk.E, pady=4)
        
    def display_new(self,direction='next'):
        action = False

        if direction == 'next':
            if self.display + 1 <= self.detail.shape[0]-1:
                self.display += 1
                action = True
                
        elif direction == 'back':
            if self.display - 1 >= 0:
                self.display += -1
                action = True
                
        if action:
            # change arguments
            for i in range(self.args_n):
                self.args[i].set(self.detail[self.headers[i]].iloc[self.display])
                
            self.currecnt_displayed.set(str(self.display+1) + "/" + str(self.detail.shape[0]))    

    def crossref_query_doi(self,doi_to_find):
        
        result_final = [] # list to save outcomes
        api_url = "https://api.crossref.org/works/" # url of the api
        url = api_url + doi_to_find # create url
        request = Request(url) #request url
        request.add_header("User-Agent", 
                           "Econ PhD Candidate (https://github.com/jacekb95; mailto:jacek.barszczewski@bse.eu)") # polite access
        
        try:
            data = json.loads(urlopen(request).read()) # read data from the appi
            item = data["message"] # select list with returned titles
            
            author_family = "" # create sting with names and sunames of authors
            for i in range(len(item['author'])):
                author_family += item['author'][i]['family'] + ", " + item['author'][i]['given'] + " and "

            candidate = [item["title"][0], author_family[:-5], item['container-title'][0],\
                         item['issued']['date-parts'][0][0],item["DOI"],\
                             1]
                
            result_final.append(candidate)
                                
            result_final = pd.DataFrame(result_final, columns= self.headers + ['similarity'])
            result_final['coef'] = 0.8*result_final['similarity'] + 0.2*result_final.iloc[:,3]/result_final.iloc[:,3].max()
            result_final = result_final.sort_values(by=['coef'],ascending=False)
            return {"success": True, "result": result_final}
        
        except HTTPError as httpe:
            return {"success": False, "exception": httpe}   

               
    def crossref_query_title(self,title_to_find):
        
        result_final = [] # list to save outcomes
        api_url = "https://api.crossref.org/works?" # url of the api
        url = api_url + urlencode({"rows": "10", "query.bibliographic": title_to_find}, quote_via=quote_plus) # create url
        request = Request(url) #request url
        request.add_header("User-Agent", "Econ PhD Candidate (https://github.com/jacekb95; mailto:jacek.barszczewski@bse.eu)") # polite access
        title_to_compare = re.sub('\W+','', title_to_find).lower() # format of the title to compare
        
        try:
            data = json.loads(urlopen(request).read()) # read data from the appi
            items = data["message"]["items"] # select list with returned titles
            
            if items != []: # if list is not empty

                for item in items: # loop over titles
                
                    try:
                        if item["title"] != []:
                            author_family = "" # create sting with names and sunames of authors
                            for i in range(len(item['author'])):
                                author_family += item['author'][i]['family'] + ", " + item['author'][i]['given'][0] + "., "
                            
                            candidate = [item["title"][0], author_family[:-2], item['container-title'][0],\
                                         item['issued']['date-parts'][0][0],item["DOI"],\
                                             ratio(re.sub('\W+','', item["title"][0]).lower(), title_to_compare)]
                    except KeyError:
                        continue
                    
                    if candidate[-1] > 0.75:
                        result_final.append(candidate)
     
            if result_final == []:
                return {"success": False}

            else:
                result_final = pd.DataFrame(result_final, columns= self.headers + ['similarity'])
                result_final['coef'] = 0.8*result_final['similarity'] + 0.2*result_final.iloc[:,3]/result_final.iloc[:,3].max()
                result_final = result_final.sort_values(by=['coef'],ascending=False)
                return {"success": True, "result": result_final}
            
        except HTTPError as httpe:
            return {"success": False, "exception": httpe}   
    
    def close_window(self):
        self.top.destroy()
    
    def create_bib(self):
        
        # perpare citation_key 
        citation_key = self.detail['Authors'][0].split(',')[0] + str(self.detail['Year'][0]) 
        
        # open file
        file = open(self.out + '//' + citation_key + '.bib','w')
        
        # write information to file
        file.write("@article{" + citation_key + ",\n")
        file.write("author = {" + self.detail['Authors'][0] + "}, \n")
        file.write("doi = {" + str(self.detail['DOI'][0]) + "}, \n")
        file.write("journal = {" + self.detail['Journal'][0] + "}, \n")
        file.write("title = {{" + self.detail['Title'][0] + "}}, \n")
        file.write("year = {" + str(self.detail['Year'][0]) + "}, \n")
        file.write("}")
        file.close()
        
        self.top.destroy()
        
# function which loads saved directories
def read_directories():
    with open(PATH + 'data/directories.txt', 'r') as file:
        directories = json.loads(file.read().replace("'", "\""))
    return directories

def copy_to_clip(object_to_copy):
    clip = tk.Tk()
    clip.withdraw()
    clip.clipboard_clear()
    clip.clipboard_append(object_to_copy)
    clip.destroy()
    
# function which saves directories
class save_directory_win:
    def __init__(self):
        self.directories = read_directories()
        self.new_directory = filedialog.askdirectory(title = "Choose new directory")
        self.new_dir_split = self.new_directory.split('/')
        self.window()

    def window(self):
        #window
        self.name = tk.Toplevel()
        self.name.title("Directory name")
        
        lbl0 = tk.Label(self.name, text="Directory", font=("Arial",11),anchor='w')
        lbl0.grid(row=0,column=0)
        
        dir_wind = tk.Entry(self.name,textvariable= tk.StringVar(self.name,value=self.new_directory),width=50)
        dir_wind.grid(row=0, columnspan=2, column=1)
        
        lbl1 = tk.Label(self.name, text="Directory name", font=("Arial",11),anchor='w')
        lbl1.grid(row=1,column=0)
        
        dir_name = tk.Entry(self.name,textvariable=tk.StringVar(self.name,value=self.new_dir_split[-1]),width=50)
        dir_name.grid(row=1, columnspan=2, column=1)
        
        self.name.button1 = tk.Button(self.name, text='Save', font=("Arial",11),command=lambda: self.save_directory(dir_wind.get(),\
                                 dir_name.get())).grid(row=3, column=1, sticky=tk.W+tk.E, pady=4)
        self.name.button2 = tk.Button(self.name, text='Cancel', font=("Arial",11),command=self.name.destroy).grid(row=3, column=2,sticky=tk.W+tk.E, pady=4)


    def save_directory(self,dir_wind,dir_name):
        self.directories[dir_name] = dir_wind
       
        with open(PATH + 'data/directories.txt', 'w') as file:
            file.write(str(self.directories))
            
        self.name.destroy()

class delete_directory_win:
    def __init__(self):
        self.window()       
        
    def window(self):
        #window
        self.directories = read_directories()    
        self.delete = tk.Toplevel()
        self.delete.title("Delete directory")
        
        lbl0 = tk.Label(self.delete, text="Select", font=("Arial",11),anchor='w')
        lbl0.grid(row=0,column=0)
        
        self.list = tkk.Combobox(self.delete,width=47,state='readonly')
        self.list['values']= list(self.directories.keys())
        self.list.current(0) 
        self.list.grid(column=1, columnspan = 2 ,row=0,sticky='w')  
        
        self.delete.button1 = tk.Button(self.delete, text='Delete', font=("Arial",11),\
                                      command=lambda: self.delete_directory()).grid(row=3, column=1, sticky=tk.W+tk.E, pady=4)
        self.delete.button2 = tk.Button(self.delete, text='Cancel', font=("Arial",11),command=self.delete.destroy).grid(row=3, column=2,sticky=tk.W+tk.E, pady=4)

    def updtcblist(self):
        #self.directory_data = read_directories()
        #self.list['values'] = list(self.directory_data.keys())
        #self.list.current(0)
        #self.list.grid(column=1, columnspan = 2 ,row=0,sticky='w')  
        self.delete.destroy()
        self.window()
        

    def delete_directory(self):
        self.directory_data = read_directories()
        to_delete = self.list.get()
        del self.directory_data[to_delete]
        
        with open(PATH + 'data/directories.txt', 'w') as file:
            file.write(str(self.directory_data))
        
        self.updtcblist()

    
def hello():
    print("Hello World!!!")