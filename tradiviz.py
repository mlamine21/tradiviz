
from tkinter import *
from tkinter.ttk import Combobox, Treeview, Progressbar
from mongoUtils import *
from functools import partial
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from  matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.patches as mpatches
from matplotlib.widgets import RangeSlider
import networkx as nx
import csv


class Tradiviz():

    client = None
    db = None
    filtered_matrix = None
    ax= None
    thres_min = 0
    thres_max = 1
    time_min = 0
    time_max = 1
    size_nodes = 2500

    def __init__(self) -> None:
        pass

    def initGUI():
        root = Tk()
        root.title("TraDiViz")
        # width= root.winfo_screenwidth()
        # height= root.winfo_screenheight()
        # #setting tkinter window size
        # root.geometry("%dx%d" % (width, height))
        root.geometry('1200x800')

        m = PanedWindow(orient=HORIZONTAL)
        m.pack(fill=BOTH, expand=1)

        left_frame = Frame(m)

        right_frame = Frame(m)
        m.add(left_frame)
        m.add(right_frame)
        ########################################
        #SERVER MENU
        ######################################
        server_frame = Frame(left_frame,  highlightbackground="grey", highlightthickness=2)
        # server_frame = Frame(left_frame)

        Label(server_frame,text ="Server configuration", font='Arial 12 bold').grid(row=0,column=0, columnspan=5, pady=10, sticky="w")

        Label(server_frame,text ="Host : ").grid(row=1,column=0, padx=5, sticky="w")
        host = Entry(server_frame, width = 10)
        host.insert(0,"127.0.0.1")
        host.grid(row=1,column=1, padx=5, sticky="w")

        Label(server_frame,text ="Port : ").grid(row=1,column=2, padx=5, sticky="w")
        port = Entry(server_frame, width = 10)
        port.insert(0,27018)
        port.grid(row=1,column=3, padx=5, sticky="w")

        Label(server_frame,text ="Username : ").grid(column = 0, row = 2, padx=5, sticky="w")
        username = Entry(server_frame, width = 10)
        username.insert(0,"amine")
        username.grid(column = 1, row = 2, padx=5, sticky="w")

        Label(server_frame,text ="Password : ").grid(column = 2, row = 2, padx=5, sticky="w")
        password = Entry(server_frame, width = 10, show="*")
        password.insert(0,"password")
        password.grid(column = 3, row = 2, padx=5, sticky="w")


        connect_button = Button(server_frame, text = "Connect", command= connect)
        connect_button.grid(column = 1, row = 4, columnspan=2, pady=10)
        client = ''

        status_frame = Frame(server_frame)
        Label(status_frame,text ="Status : ").pack(side="left")
        status = Label(status_frame)
        status.config(text="Disconnected")
        status.pack()

        status_frame.grid(column=1, row=5, columnspan=2,rowspan=4, padx=5,pady=5)

        for i in range(5):
            server_frame.grid_rowconfigure(0, weight=1)
            server_frame.grid_columnconfigure(i, weight=1)
        server_frame.pack(side='top', fill='both')
        # server_frame.configure(border=2, borderwidth=10)

        #####################################################
        #Database menu
        #####################################################
        database_frame = Frame(left_frame, highlightbackground="grey", highlightthickness=2)
        for i in range(5):
            database_frame.grid_rowconfigure(i, weight=1)
            database_frame.grid_columnconfigure(i, weight=1)
        # database_frame.grid_columnconfigure(1, weight=1)
        Label(database_frame,text ="Database").grid(column = 0, row = 0, padx=10, pady=5, sticky="w")
        db_changed=StringVar()
        database_choice = Combobox(database_frame, values=[], textvariable=db_changed)
        database_choice.grid(column=1, row=0, padx=10, pady=5, sticky="w")
        database_choice.bind("<<ComboboxSelected>>", chooseDB)


        Label(database_frame,text ="Sessions").grid(column = 0, row = 1, padx=10, pady=5)
        sessions = Listbox(database_frame, selectmode = "extended", exportselection=False)  
        sessions.grid(column = 0, row = 2, padx=10, pady=5, sticky='nswe', rowspan=3)

        Label(database_frame,text ="Schemes").grid(column = 1, row = 1, padx=10, pady=5)
        schemes = Listbox(database_frame, selectmode = "extended", height=5, exportselection=False)  
        schemes.grid(column = 1, row = 2, padx=10, pady=5, sticky='nswe')
        schemes.bind("<<ListboxSelect>>", updateLabels)

        Label(database_frame,text ="Annotators").grid(column = 1, row = 3, padx=10, pady=5)
        annotators = Listbox(database_frame, height=5, exportselection=False)  
        annotators.grid(column = 1, row = 4, padx=10, pady=5, sticky='nswe')
        # schemes.bind("<<ListboxSelect>>", updateLabels)

        # Label(database_frame,text ="Labels").grid(column = 2, row = 1, padx=10, pady=5)

        labels = Treeview(database_frame, columns=['id', 'label', 'shortname'], selectmode='extended')
        labels['show'] = 'headings'
        labels.heading('id', text='id')
        labels.column('id', width="10")
        labels.heading('label', text='label')
        labels.heading('shortname', text='shortname')
        # labels = Listbox(database_frame, selectmode = "multiple", exportselection=False)  
        labels.grid(column = 0, row =5, padx=10, pady=5, sticky='nswe', columnspan=2)
        labels.bind('<1>', editTreeCell)
        database_frame.pack(fill="both")
        #####################################
        #Transition matrix
        #####################################
        transition_frame =  Frame(left_frame, highlightbackground="grey", highlightthickness=2)

        connect_button = Button(transition_frame, text = "Generate transition matrix", command= generateMatrix)
        connect_button.grid(column = 0, row = 0, pady=10, sticky='w')

        matrix_frame = Frame(transition_frame, highlightbackground="grey", highlightthickness=2)
        matrix_frame.grid(row=1,column=0,padx=10)


        transition_frame.pack(side='left')

        # left_frame.pack(side="left")


        ################################################
        # Plot frame
        ################################################
        fig, ax= plt.subplots()
        ax.axis(False)
        axthres = fig.add_axes([0.25, 0, 0.6, 0.05])
        axtime = fig.add_axes([0.25, 0.9, 0.6, 0.05])
        # fig.set_size_inches(fig.get_size_inches()[0]*1.2, fig.get_size_inches()[1]*1.2)
        thres_slider = RangeSlider(
            ax=axthres,
            label='Threshold',
            valmin=0,
            valmax=1,
            valinit=[0.8, 1],
            valstep=0.05,
            dragging=True
        )
        thres_slider.on_changed(updateDiagram)

        time_slider = RangeSlider(
            ax=axtime,
            label='Time range',
            valmin=0,
            valmax=1,
            valinit=[0, 1],
            valstep=0.25,
            dragging=True,

        )
        canvas = FigureCanvasTkAgg(fig, right_frame)
        time_slider.on_changed(updateTimeRange)
        # toolbar = NavigationToolbar2Tk(canvas, right_frame)
        # toolbar.update()
        canvas._tkcanvas.pack(fill=BOTH, expand=True)
        # right_frame.pack(side="right", fill="both", expand=True)



        root.mainloop()  
