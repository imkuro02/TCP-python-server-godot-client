extends Control

const Packet = preload("res://Scripts/Packet.gd")

@onready var chatbox = $CanvasLayer/VBoxContainer/RichTextLabel
@onready var input = $CanvasLayer/VBoxContainer/LineEdit
@onready var logout = $Logout

var MAIN 

func _ready():
	MAIN = get_tree().root.get_node('Main')
	
func receive(text: String):
	chatbox.text += text
	
func send(text: String):
	if len(text) > 0:
		var p: Packet = Packet.new('Chat',[input.text])
		MAIN.send_packet(p)
		input.text = ""
		
func _input(event: InputEvent):
	if event is InputEventKey and event.pressed:
		match event.keycode:
			KEY_ENTER:
				send(input.text)
				input.text = ""
				input.grab_focus()
			KEY_ESCAPE:
				input.release_focus()


func _on_logout_pressed():
	var p: Packet = Packet.new('Disconnect')
	MAIN.send_packet(p)
	
