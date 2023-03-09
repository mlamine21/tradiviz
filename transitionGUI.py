
# from tkinter import *                
from tkinter import *
from tkinter.ttk import Combobox, Treeview
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
##NEEDS pillow==9.0.0 and matplotlib 3.7.0
client = None
db = None
filtered_matrix = None
ax= None
def connect():
    global client
    client = connectDB(host.get(), int(port.get()), username.get(), password.get())
    try :
        client.server_info()
        # print(client)
        status.config(text="Connected")
        all_db = client.list_database_names()  
        for db in all_db:
            if(db not in database_choice['values'] and 
            ('admin' not in db and 'config' not in db and 'local' not in db)):
                database_choice['values'] = (*database_choice['values'], str(db))
    except pymongo.errors.ServerSelectionTimeoutError as err:
        status.config(text="Connection failed. \nCheck your server settings.")
        print(err)

def chooseDB(event):
    global db
    sessions.delete(0,END)
    schemes.delete(0,END)
    # print(database_choice.get)
    chosen_db = db_changed.get()
    db = client[chosen_db]
    sessions_temp = db["Sessions"]
    sessions_names,sessions_ids = getCollectionNamesIds(sessions_temp)
    sessions_names.sort()
    for s in sessions_names:
        sessions.insert(sessions.size(),s)

    schemes_temp = db["Schemes"]
    schemes_names,schemes_ids = getCollectionNamesIds(schemes_temp)
    for s in schemes_names:
        schemes.insert(schemes.size(),s)
    
    annotators_temp = db["Annotators"]
    annotators_names,annotators_ids = getCollectionNamesIds(annotators_temp)
    for a in annotators_names:
        annotators.insert(annotators.size(),a)

def updateLabels(event):
    global db
    clearTree(labels)
    selection_id = schemes.curselection()
    selection_names = [schemes.get(i) for i in selection_id]
    schemes_temp = db["Schemes"]
    idx=0
    for s in schemes_temp.find():
        if(s["name"] in selection_names):
            if("labels" in s.keys()):
                for l in s["labels"]:
                    labels.insert('', 'end', l['name'], values=(idx, l['name']))
                    idx+=1
            else:
                print("No labels found")
            
def clearTree(tree):
    for item in tree.get_children():
      tree.delete(item)

def generateMatrix():
    global db
    global filtered_matrix
    global ax
    chosen_db = db_changed.get()
    db = client[chosen_db]
    annotators_collection = db["Annotators"]
    annotators_names,annotators_ids = getCollectionNamesIds(annotators_collection)
    #Get ObjectID of selected annotator for the annotation to add
    annotator_id = annotators_ids[(getListBoxSelection(annotators))[0]]

    sessions_temp = db["Sessions"]
    sessions_names,sessions_ids = getCollectionNamesIds(sessions_temp)
    schemes_temp = db["Schemes"]
    schemes_names,schemes_ids = getCollectionNamesIds(schemes_temp)
    
    roles_temp = db["Roles"]
    roles_names, roles_ids = getCollectionNamesIds(roles_temp)

    annotations = db["Annotations"]
    annotations_data = db["AnnotationData"]
    all_sessions_matrix = np.zeros((len(labels.get_children()),len(labels.get_children())))
    for session in getListBoxSelection(sessions):
        all_roles = []
        for scheme in getListBoxSelection(schemes):
            #Get the annotation files
            annotation = annotations.find({
            "session_id":sessions_ids[sessions_names.index(sessions.get(session))],
            "annotator_id":annotator_id, 
            "scheme_id":schemes_ids[schemes_names.index(schemes.get(scheme))]})
            annotation_data_id = (annotation[0])["data_id"]
            annotation_data_entry = (annotations_data.find({"_id":annotation_data_id}))[0]
            labels_data = annotation_data_entry["labels"]
            label_matrix = pd.DataFrame(columns=[0,1,2])
            for label in labels_data:
                label_matrix.loc[labels_data.index(label)] = [label["from"], label["to"], label["id"]]
            all_roles.append(label_matrix)
        if(len(all_roles)==2):
            final_matrix = combineRolesMatrices(all_roles[0], all_roles[1], ((schemes_temp.find())[0])['labels'] )
        else:
            final_matrix = all_roles[0]  
        
        transition = getTransitions(final_matrix, normalize=False)
        # print(transition)
        
        # print(len(selection), len(filtered_matrix))
        all_sessions_matrix+=transition.values
    
    all_sessions_normalized = normalizeTransitions(all_sessions_matrix)
    # all_sessions_normalized = all_sessions_matrix
    normalized_transitions_df = pd.DataFrame(data = all_sessions_normalized)
    label_vals = labels.get_children()
    selection = labels.selection()
    filtered_matrix = filterTransitionMatrix(normalized_transitions_df, label_vals, selection)
    
    for child in matrix_frame.winfo_children():
        child.destroy()
            
    for i in range(len(selection)+1):
        for j in range(len(selection)+1):
            e = Entry(matrix_frame, width=5)
            e.grid(row=i, column=j)
            if(i==0 and j==0):
                e.insert(END, " ")
            elif(i==0 or j==0):
                val = selection[i-1] if j==0 else selection[j-1]
                e.insert(END, val)
            else:
                e.insert(END, filtered_matrix.iloc[i-1,j-1])
            e.config(state=DISABLED)
    # with open("matrix.csv", "w", newline='') as f:
    #     writer = csv.writer(f, delimiter=',')
    #     for i in range(len(filtered_matrix)):
    #         writer.writerow(filtered_matrix.iloc[i])


    drawTransitionDiagram(filtered_matrix, threshold_min=0.8, threshold_max=1)
    return

def combineRolesMatrices(data_role1, data_role2, labels_role1):
    #Change counselor labels {0:18} -> {14: 32} 
    data_role2[2] = data_role2[2].apply(lambda x:x+len(labels_role1))

    # combine client and counselor data 
    merged = [data_role1, data_role2]
    result = pd.concat(merged)
    #sort client and cousnelor data based on timing (start time is first column)
    result = result.sort_values(0)
    
    return result

def normalizeTransitions(transition_matrix):
    return (transition_matrix/transition_matrix.sum(axis=1,keepdims=1))

def getListBoxSelection(listbox): 
    selected_items = []   
    for i in listbox.curselection():
        selected_items.append(i)
    return selected_items

def filterTransitionMatrix(matrix, all_labels, selection):
    new_matrix = matrix.copy()
    for i in range(len(all_labels)):
        if(all_labels[i] not in selection):
            new_matrix.drop(i, inplace=True, axis=0)
            new_matrix.drop(i, inplace=True, axis=1)
    return new_matrix

def getTransitions(matrix,normalize = False, display=False):
    column_states = matrix.iloc[:,2].tolist()
    
    #Create transition matrix
    transitions = pd.crosstab(pd.Series(column_states[1:],name='Next'),pd.Series(column_states[:-1],name='Current'), normalize=normalize)
    
    category_dict = getDictFromTree(labels)
    transitions = transitions.reindex(index = category_dict.keys(), columns=category_dict.keys(), fill_value=0)
    if(display) : print(transitions)
    return transitions


def getDictFromTree(tree):
    value_dict = {}

    for x in tree.get_children():
        key = tree.item(x)["values"][0]
        value = tree.item(x)["values"][1]
        value_dict[key] = value
    return value_dict

def editTreeCell(event):
    if labels.identify_region(event.x, event.y) == 'cell':
        # the user clicked on a cell
        def ok(event):
            """Change item value."""
            labels.set(item, column, entry.get())
            entry.destroy()

        column = labels.identify_column(event.x)  # identify column
        if('3' in column):
            item = labels.identify_row(event.y)  # identify item
            value = labels.set(item, column)
            x, y, width, height = labels.bbox(item, column) 
            entry = Entry(labels)  # create edition entry
            entry.place(x=x, y=y, width=width, height=height,
                        anchor='nw')  # display entry on top of cell
            entry.insert(0, value)  # put former value in entry
            entry.bind('<FocusOut>', ok)  
            entry.bind('<Return>', ok)  # validate with Enter
            entry.focus_set()
    else:
        return
    return


def _get_markov_edges(Q, role=''):
    edges = {}
        
    for col in Q.columns:
        for idx in Q.index:
#             if(isCtMISCOPE(idx) and isCtMISCOPE(col)):
            if(Q.loc[idx,col]!=0):
                edges[(idx, col)] = round(Q.loc[idx,col],2)
    return edges

def drawTransitionDiagram(transitions, threshold_min=0.9, threshold_max=1):
    global ax, db
    # pprint(edges_wts)
    ax.cla()
    G = nx.MultiDiGraph(ax=ax)
    # print(transitions.columns)
    G.add_nodes_from(transitions)
    
    # Add edges with transition probabilities > threshold
    edges_wts = _get_markov_edges(transitions)
    for k,v in edges_wts.items():
        tmp_origin, tmp_destination = k[0], k[1]
        if(v>threshold_min and v<=threshold_max):
            G.add_edge(tmp_origin, tmp_destination, weight = v, label = v)

    # Position the nodes in circular layout
    pos = nx.circular_layout(G)
    edge_labels = {(x[0],int(x[1])): G.get_edge_data(*x)['label']  for x in G.edges}
    mapping = {}
    
    #Change position of edges labels for self-transitions (transitions from node to same node)
    # If we do not apply this modification, self-transitions values will not be visible
    for x in G.edges:
        if(x[0] == x[1]):
            if(x[0]>0 and x[0]<(len(G.edges)/2)):
                edge_labels[(x[0],x[1])]= str(G.get_edge_data(*x)['label'])+"\n"*7
            else:
                edge_labels[(x[0], x[1])] = 5*"\n"+str(G.get_edge_data(*x)['label'])

        else:
            edge_labels[(x[0],x[1])]= G.get_edge_data(*x)['label']

    #Map color to differentiate client from counselor
    color_map = []
    schemes_temp = db["Schemes"]
    nb_labels_role1 = len(((schemes_temp.find())[0])["labels"])
    for node in G:
        if node < nb_labels_role1:
            color_map.append('#f2bdb6')
        else: 
            color_map.append('#bee9eb')    

    for i in range(len(labels.get_children())):
        mapping[i] = labels.get_children()[i]
    G = nx.relabel_nodes(G, mapping)

    nx.draw_networkx_edge_labels(G, pos, edge_labels, label_pos=0.2, font_size=15, alpha=1, ax=ax)
    nx.draw_circular(G, with_labels= True, font_size=13, arrowsize=10, node_size=2500,node_color=color_map, ax=ax, alpha=0.9)
    # plt.show()
    # ax.update()
    canvas.draw()



def updateDiagram(val):
    global filtered_matrix
    # global ax
    # ax.cla()
    drawTransitionDiagram(filtered_matrix, val[0], val[1])

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
canvas = FigureCanvasTkAgg(fig, right_frame)

# toolbar = NavigationToolbar2Tk(canvas, right_frame)
# toolbar.update()
canvas._tkcanvas.pack(fill=BOTH, expand=True)
# right_frame.pack(side="right", fill="both", expand=True)



root.mainloop()  