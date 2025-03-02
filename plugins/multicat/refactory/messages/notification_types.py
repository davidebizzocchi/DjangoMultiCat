from cat.looking_glass.stray_cat import MSG_TYPES


msg_types = list(MSG_TYPES.__dict__["__args__"])
msg_types.append("json-notification")
MSG_TYPES.__dict__["__args__"] = tuple(msg_types)