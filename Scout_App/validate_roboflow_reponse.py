def validate_api_response(data):
    # check that response has a list or data
    if not isinstance(data, list) or len(data) != 1:
        return False

    item = data[0]

    # check top level keys
    required_keys = {"count_objects", "output_image", "predictions"}
    if not isinstance(item, dict) or not required_keys.issubset(item.keys()):
        return False

    # Validate number of predicted objects
    if not isinstance(item["count_objects"], int):
        return False

    # Validate the returned image
    if not isinstance(item["output_image"], str) or not item["output_image"]:
        return False

    # Validate predictions
    predictions = item["predictions"]
    if not isinstance(predictions, dict):
        return False

    # Check if 'predictions' field is empty and early return success
    if "predictions" in predictions:
        if isinstance(predictions["predictions"], list) and len(predictions["predictions"]) == 0:
            return True

    # Validate image inside predictions
    if "image" not in predictions or not isinstance(predictions["image"], dict):
        return False

    image = predictions["image"]
    if not all(k in image for k in ("width", "height")):
        return False
    if not all(isinstance(image[k], (int, float)) for k in ("width", "height")):
        return False

    # Validate predictions list inside predictions
    if "predictions" not in predictions or not isinstance(predictions["predictions"], list):
        return False

    for pred in predictions["predictions"]:
        if not isinstance(pred, dict):
            return False
        required_pred_keys = {"width", "height", "x", "y", "confidence", "class_id", "class", "detection_id",
                              "parent_id"}
        if not required_pred_keys.issubset(pred.keys()):
            return False
        if not isinstance(pred["class"], str) or not pred["class"]:
            return False
        if not isinstance(pred["detection_id"], str) or not pred["detection_id"]:
            return False
        if not isinstance(pred["parent_id"], str) or not pred["parent_id"]:
            return False

    return True
