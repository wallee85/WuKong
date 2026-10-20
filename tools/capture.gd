extends Node

var frames := 0


func _process(_delta: float) -> void:
	frames += 1
	if frames == 30:
		var image := get_viewport().get_texture().get_image()
		image.save_png("res://capture.png")
		print("CAPTURED")
		get_tree().quit()












