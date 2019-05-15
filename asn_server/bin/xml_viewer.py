from Tkinter import *
from lxml import etree, objectify
import sys
from collections import defaultdict

data_dict = defaultdict(list)

class XmlViewer(Frame):

    def __init__(self, parent, nodes):
        Frame.__init__(self, parent)

        canvas_height = 1000.0
        canvas_width = 1500.0
        self.input_dict = defaultdict(list)
        self.output_dict = defaultdict(list)
        self.pi_children = defaultdict(list)
	
        # create a canvas
	self.canvas = Canvas(self, width=canvas_width, height=canvas_height)
	self.canvas.pack(fill=BOTH, expand=TRUE)
	 
        # this data is used to keep track of a dragged pi and it's links
        self._drag_data = {"x": 0.0, "y": 0.0, "item": None, "children": None}
        self._drag_links = {"input": None, "output": None}

	x= 200.0
	y=300.0
        pi_width=0

	# create box for each pi
        for n in nodes:
	    x=x+pi_width*1.2
	    if x>canvas_width-400:
		x=400.00
		y=y+500.00
	    	if y>canvas_height:
		    y=300.00
            pi_width=self.create_box((x, y), "white",objectify.fromstring(n).get("pi_id"),
                               objectify.fromstring(n).algorithm)

        # create links between ports
        #print 'input to inputdic***********',len(self.input_dict)
        self.create_links(self.input_dict, self.output_dict)

	# add binding for clicking on background
        self.canvas.bind("<Button-1>", self.on_canvas_press)

        # add bindings for clicking, dragging and releasing over any object with the "pi" tag
        self.canvas.tag_bind("pi", "<ButtonPress-1>", self.on_box_press)
        self.canvas.tag_bind("pi", "<ButtonRelease-1>", self.on_box_release)
        self.canvas.tag_bind("pi", "<B1-Motion>", self.on_box_motion)

    def create_links(self, input_dict2, output_dict2):


        for key_dict in input_dict2:
           input_dict = input_dict2[key_dict]
           output_dict = output_dict2[key_dict]
           #print 'in create links,key_dict', key_dict
           #print 'in create links,input_dict', input_dict

           for key in range(len(input_dict)):
            #print 'key = ', key
            #print 'in create links,input_dict elem', input_dict[key][key_dict]
            #print 'checking ',input_dict[key][key_dict][1],'!=',output_dict[0][key_dict][1]
            if input_dict[key][key_dict][1]!=output_dict[0][key_dict][1] :
                #print 'generating link: ',(key,input_dict[key][key_dict][1] ),(key,output_dict[0][key_dict][1])
                self.canvas.create_line(output_dict[0][key_dict][0][0], output_dict[0][key_dict][0][1], input_dict[key][key_dict][0][0],
                                        input_dict[key][key_dict][0][1], fill = "blue",arrow="last", dash=(3,5), width=2,
                                        tags=("link", input_dict[key][key_dict][1], output_dict[0][key_dict][1]))


    def create_box(self, coord, color, pi_name, algorithms):
        #Create a box at the given coordinate
        (x, y) = coord    
        
	#define height and width for pi object
        height = 0
        width=0
        for a in algorithms:
            height = height + 1
            name=str(a.get("executable")+a.parameter.get('param'))
            if width < len(name):
                width=len(name)
        width=width+0.0
        width=width*10
        if width<120 :
            width=120.0

	#create pi object with pi name
	#and save the following objects that are drawn onto the pi object in tuple "children"
        pi_index = self.canvas.create_rectangle(x-width/2, y-height*50-15, x+width/2, y+height*50,
                                     fill=color, tags="pi")
        children = (pi_index,)
        children = children + (self.canvas.create_text(x, y-height*50-5, text=pi_name),)
        children = children +(self.canvas.create_line(x-width/2+1, y-height*50+5, x+width/2-1, y-height*50+5),)

        port_row=0
	# create module objects
        for a in algorithms:
            children = children + (self.canvas.create_rectangle(x-width/2 +5, (y-height*50)+5+port_row*100, x +width/2-5,
				      (y-height*50)+95+port_row*100, fill="white"),)
            children = children +(self.canvas.create_text(x, (y-height*50)+5+port_row*100+40, text=a.get("executable")+" "+a.parameter.get("param")),)
            offset_i = 0
            offset_o = 0
            ports=a.getchildren()

            for i in ports:
                # create input boxes
                if i.get("source_pi_id"):
                    children = children + (self.canvas.create_rectangle(x-width/2+5, (y-height*50)+5+port_row*100+offset_i*15+5,
					     x -width/2+25, (y-height*50)+15+port_row*100+offset_i*15+5, 
					     tags=("input", i.get("pipe_id"), "pi"+str(pi_index))),)
                    children = children + (self.canvas.create_text(x-width/2+15, (y-height*50)+5+port_row*100+offset_i*15+5+5,
                                             text=i.get("pipe_id"), font=("Helvetica", 6)),)
                    offset_i=offset_i+1
		# create output boxes
                elif i.get("target_pi_id"):
                    children = children + (self.canvas.create_rectangle(x+width/2-25, (y-height*50)+5+port_row*100+offset_o*15+5, x+width/2-5,
                                              (y-height*50)+15+port_row*100+offset_o*15+5, tags=("output", i.get("pipe_id"), "pi"+str(pi_index))),)
                    children = children + (self.canvas.create_text(x+width/2-15, (y-height*50)+5+port_row*100+offset_o*15+5+5,
                                              text=i.get("pipe_id"), font=("Helvetica", 6)),)
                    offset_o=offset_o+1
            port_row=port_row+1

	# add to dictionary "pi_children" pi with children objects
        self.pi_children[pi_index]=children

        inputs = self.canvas.find_withtag("input")
        outputs = self.canvas.find_withtag("output")

        # port dictionarys with pipe_id: (coords, piX)
        #print 'all inputs len = ', len([(self.canvas.coords(i), self.canvas.gettags(i)[2]) for i in inputs])
        for i in inputs:
            #print 'in box ', self.canvas.gettags(i)[1]
            self.input_dict[self.canvas.gettags(i)[1]].append({self.canvas.gettags(i)[1]:(self.canvas.coords(i), self.canvas.gettags(i)[2])})
        #print 'all inputs in create box = ', [i  for i in self.input_dict]


        for o in outputs:
            self.output_dict[self.canvas.gettags(o)[1]].append({self.canvas.gettags(o)[1]:(self.canvas.coords(o), self.canvas.gettags(o)[2])})
        #print 'all ouptuts in create box = ', [i  for i in self.output_dict]

        return width
	
    def on_canvas_press(self, event):
	# if background clicked all links are becoming dashed
        if self.canvas.find_overlapping(event.x, event.y, event.x, event.y)==():
            links = self.canvas.find_withtag("link")
            for l in links:
                self.canvas.itemconfig(l, width=2, dash=(3, 5))

    def on_box_press(self, event):
        # Beginning drag of a pi object
        # record the item and its location
        item =self.canvas.find_closest(event.x, event.y)

	#connected links to pi
        connected_links_in = []
        connected_links_out = []
        links = self.canvas.find_withtag("link")
        for l in links:
            self.canvas.itemconfig(l, width=2, dash=(3, 5))
            if self.canvas.gettags(l)[1]==("pi"+str(item[0])):
                connected_links_in.append(l)
                self.canvas.itemconfig(l, width=2, dash=())
            if self.canvas.gettags(l)[2]==("pi" + str(item[0])):
                connected_links_out.append(l)
                self.canvas.itemconfig(l, width=2, dash=())
	
	# draggable items
	self._drag_data["item"] = self.pi_children[item[0]]
        self._drag_links["input"] = connected_links_in
        self._drag_links["output"] = connected_links_out

	# current position of mouse
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_box_release(self, event):
        # End drag of a pi object
        
	# links are dashed during dragging
        for i in self._drag_links["input"]:
            self.canvas.itemconfig(i, width=2, dash=())
        for o in self._drag_links["output"]:
            self.canvas.itemconfig(o, width=2, dash=())

        # reset the drag information
        self._drag_data["item"] = None
        self._drag_data["x"] = 0
        self._drag_data["y"] = 0

        self._drag_links["input"] = None
        self._drag_links["output"] = None


    def on_box_motion(self, event):
        # handle dragging of pi object
        # compute how much the mouse has moved
        delta_x = event.x - self._drag_data["x"]
        delta_y = event.y - self._drag_data["y"]

        # move the pi object and links the appropriate amount
        for item in self._drag_data["item"]:
            self.canvas.move(item, delta_x, delta_y)

        for i in self._drag_links["input"]:
            self.canvas.itemconfig(i, width=2, dash=(3, 5))
            coords = self.canvas.coords(i)
            coords[2]= coords[2]+delta_x
            coords[3]= coords[3] +delta_y
            self.canvas.coords(i, coords[0], coords[1], coords[2], coords[3])

        for o in self._drag_links["output"]:
            self.canvas.itemconfig(o, width=2, dash=(3, 5))
            coords = self.canvas.coords(o)
            coords[0]+=delta_x
            coords[1]+=delta_y
            self.canvas.coords(o, coords[0], coords[1], coords[2], coords[3])

        # record the new position
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

def parse_xml(xmlFile):
    with open(xmlFile) as f:
        xml = f.read()
        return xml

if __name__ == "__main__":

    root_as_string = parse_xml(sys.argv[1])
    root=objectify.fromstring(root_as_string)

    nodes =[]

    for element in root.getchildren():
        #print '******run Main*****'

        nodes.append(etree.tostring(element))
    root = Tk()
    root.title("Xml_viewer")
    XmlViewer(root, nodes).pack(fill="both", expand=True)
    root.mainloop()
