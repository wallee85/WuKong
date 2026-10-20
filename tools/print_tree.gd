extends SceneTree


func _init() -> void:
	var packed: PackedScene = load("res://scenes/main.tscn")
	var root := packed.instantiate()
	_dump(root, 0)
	root.free()
	quit()


func _dump(node: Node, depth: int) -> void:
	print("NODE ", "  ".repeat(depth), node.name, " <", node.get_class(), ">")
	for child in node.get_children():
		_dump(child, depth + 1)
