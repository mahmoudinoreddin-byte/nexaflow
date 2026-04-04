# cad-editor.py
from flask import Flask, render_template, request, jsonify, send_file
import json
import os
import tempfile
from datetime import datetime
import math

app = Flask(__name__)
app.secret_key = 'cad-editor-secret-key-2024'

# Dossier temporaire
TEMP_DIR = tempfile.mkdtemp()

# Stockage des données
scene_data = {
    "objects": [],
    "history": [],
    "sketches": [],
    "last_id": 0
}

# ============================================================
# ROUTES PRINCIPALES
# ============================================================

@app.route('/')
def index():
    """Sert la page HTML"""
    return render_template('tools/cad-editor.html')

@app.route('/api/objects', methods=['GET'])
def get_objects():
    """Récupère tous les objets"""
    return jsonify({
        "success": True,
        "objects": scene_data["objects"]
    })

@app.route('/api/objects', methods=['POST'])
def add_object():
    """Ajoute un objet"""
    try:
        data = request.json
        scene_data["last_id"] += 1
        
        new_object = {
            "id": scene_data["last_id"],
            "name": data.get("name", f"Object_{scene_data['last_id']}"),
            "type": data.get("type", "box"),
            "position": data.get("position", {"x": 0, "y": 0, "z": 0}),
            "rotation": data.get("rotation", {"x": 0, "y": 0, "z": 0}),
            "scale": data.get("scale", {"x": 1, "y": 1, "z": 1}),
            "material": data.get("material", "steel"),
            "visible": data.get("visible", True),
            "created_at": datetime.now().isoformat()
        }
        
        scene_data["objects"].append(new_object)
        scene_data["history"].append({
            "action": "create",
            "object_name": new_object["name"],
            "timestamp": datetime.now().isoformat()
        })
        
        return jsonify({
            "success": True,
            "object": new_object
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/objects/<int:obj_id>', methods=['PUT'])
def update_object(obj_id):
    """Met à jour un objet"""
    try:
        data = request.json
        obj = next((o for o in scene_data["objects"] if o["id"] == obj_id), None)
        
        if not obj:
            return jsonify({"success": False, "error": "Object not found"}), 404
        
        if "name" in data:
            obj["name"] = data["name"]
        if "position" in data:
            obj["position"].update(data["position"])
        if "rotation" in data:
            obj["rotation"].update(data["rotation"])
        if "scale" in data:
            obj["scale"].update(data["scale"])
        if "material" in data:
            obj["material"] = data["material"]
        if "visible" in data:
            obj["visible"] = data["visible"]
        
        return jsonify({"success": True, "object": obj})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/objects/<int:obj_id>', methods=['DELETE'])
def delete_object(obj_id):
    """Supprime un objet"""
    try:
        scene_data["objects"] = [o for o in scene_data["objects"] if o["id"] != obj_id]
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/sketch', methods=['POST'])
def save_sketch():
    """Sauvegarde un sketch"""
    try:
        data = request.json
        sketch = {
            "id": len(scene_data["sketches"]) + 1,
            "type": data.get("type"),
            "points": data.get("points", []),
            "params": data.get("params", {}),
            "timestamp": datetime.now().isoformat()
        }
        scene_data["sketches"].append(sketch)
        
        return jsonify({
            "success": True,
            "sketch_id": sketch["id"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/extrude', methods=['POST'])
def extrude_shape():
    """Extrude un sketch"""
    try:
        data = request.json
        sketch_id = data.get("sketch_id")
        depth = data.get("depth", 2.0)
        
        # Trouver le sketch
        sketch = None
        for s in scene_data["sketches"]:
            if s["id"] == sketch_id:
                sketch = s
                break
        
        if not sketch:
            return jsonify({"success": False, "error": "Sketch not found"}), 404
        
        # Créer l'objet extrudé
        scene_data["last_id"] += 1
        new_object = {
            "id": scene_data["last_id"],
            "name": f"Extrude_{sketch['type']}",
            "type": "extrusion",
            "position": {"x": 0, "y": 0, "z": 0},
            "rotation": {"x": 0, "y": 0, "z": 0},
            "scale": {"x": 1, "y": 1, "z": 1},
            "material": data.get("material", "steel"),
            "visible": True,
            "depth": depth,
            "created_at": datetime.now().isoformat()
        }
        
        scene_data["objects"].append(new_object)
        
        # Nettoyer le sketch utilisé
        scene_data["sketches"] = [s for s in scene_data["sketches"] if s["id"] != sketch_id]
        
        return jsonify({"success": True, "object": new_object})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/export/stl', methods=['POST'])
def export_stl():
    """Export STL"""
    try:
        data = request.json
        objects_to_export = data.get("objects", scene_data["objects"])
        
        # Générer le contenu STL
        stl_content = "solid CAD_Export\n"
        for obj in objects_to_export:
            pos = obj.get("position", {"x": 0, "y": 0, "z": 0})
            scale = obj.get("scale", {"x": 1, "y": 1, "z": 1})
            
            stl_content += f"  facet normal 0 1 0\n"
            stl_content += f"    outer loop\n"
            x, y, z = pos["x"], pos["y"], pos["z"]
            sx, sy, sz = scale["x"], scale["y"], scale["z"]
            
            # Cube simple pour l'export
            vertices = [
                (x-sx, y-sy, z-sz), (x+sx, y-sy, z-sz), (x+sx, y+sy, z-sz),
                (x-sx, y-sy, z+sz), (x+sx, y-sy, z+sz), (x+sx, y+sy, z+sz)
            ]
            
            for i in range(3):
                stl_content += f"      vertex {vertices[i][0]} {vertices[i][1]} {vertices[i][2]}\n"
            stl_content += f"    endloop\n"
            stl_content += f"  endfacet\n"
        
        stl_content += "endsolid CAD_Export\n"
        
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.stl"
        filepath = os.path.join(TEMP_DIR, filename)
        
        with open(filepath, 'w') as f:
            f.write(stl_content)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/export/obj', methods=['POST'])
def export_obj():
    """Export OBJ"""
    try:
        data = request.json
        objects_to_export = data.get("objects", scene_data["objects"])
        
        obj_content = f"# CAD Export\n# Generated: {datetime.now().isoformat()}\n\n"
        
        vertex_offset = 1
        for idx, obj_data in enumerate(objects_to_export):
            obj_content += f"o {obj_data.get('name', f'Object_{idx}')}\n"
            
            pos = obj_data.get("position", {"x": 0, "y": 0, "z": 0})
            scale = obj_data.get("scale", {"x": 1, "y": 1, "z": 1})
            
            x, y, z = pos["x"], pos["y"], pos["z"]
            sx, sy, sz = scale["x"], scale["y"], scale["z"]
            
            vertices = [
                (x-sx, y-sy, z-sz), (x+sx, y-sy, z-sz),
                (x+sx, y+sy, z-sz), (x-sx, y+sy, z-sz),
                (x-sx, y-sy, z+sz), (x+sx, y-sy, z+sz),
                (x+sx, y+sy, z+sz), (x-sx, y+sy, z+sz)
            ]
            
            for v in vertices:
                obj_content += f"v {v[0]} {v[1]} {v[2]}\n"
            
            obj_content += "\n"
            
            faces = [
                [1,2,3], [1,3,4], [5,7,6], [5,8,7],
                [1,5,6], [1,6,2], [3,7,8], [3,8,4],
                [1,4,8], [1,8,5], [2,6,7], [2,7,3]
            ]
            
            for face in faces:
                obj_content += f"f {face[0]+vertex_offset-1} {face[1]+vertex_offset-1} {face[2]+vertex_offset-1}\n"
            
            obj_content += "\n"
            vertex_offset += 8
        
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.obj"
        filepath = os.path.join(TEMP_DIR, filename)
        
        with open(filepath, 'w') as f:
            f.write(obj_content)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/history', methods=['GET'])
def get_history():
    """Récupère l'historique"""
    return jsonify({"success": True, "history": scene_data["history"]})

@app.route('/api/clear', methods=['DELETE'])
def clear_scene():
    """Efface la scène"""
    scene_data["objects"] = []
    scene_data["sketches"] = []
    return jsonify({"success": True})

# ============================================================
# LANCEMENT
# ============================================================

if __name__ == '__main__':
    print("=" * 50)
    print("CAD EDITOR - SERVEUR FLASK")
    print("=" * 50)
    print(f"📁 Dossier temporaire: {TEMP_DIR}")
    print(f"🌐 Accédez à: http://localhost:5000")
    print("=" * 50)
    
    # Activer CORS pour éviter les erreurs de connexion
    from flask_cors import CORS
    CORS(app)
    
    app.run(debug=True, host='127.0.0.1', port=5000)
