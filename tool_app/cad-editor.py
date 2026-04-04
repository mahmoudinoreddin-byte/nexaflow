# cad-editor.py
from flask import Flask, render_template, request, jsonify, send_file
import json
import os
import tempfile
from datetime import datetime
import base64
import re

app = Flask(__name__)
app.secret_key = 'cad-editor-secret-key-2024'

# Dossier pour stocker les exports temporaires
TEMP_DIR = tempfile.mkdtemp()

# Stockage des données de la scène en mémoire (pour démonstration)
# Dans une application réelle, vous utiliseriez une base de données
scene_data = {
    "objects": [],
    "history": [],
    "last_id": 0
}

# ============================================================
# ROUTES PRINCIPALES
# ============================================================

@app.route('/')
def index():
    """Route principale - sert la page HTML"""
    return render_template('tools/cad-editor.html')

@app.route('/api/scene', methods=['GET'])
def get_scene():
    """Récupère toutes les données de la scène"""
    return jsonify({
        "success": True,
        "data": scene_data
    })

@app.route('/api/objects', methods=['GET'])
def get_objects():
    """Récupère la liste des objets 3D"""
    return jsonify({
        "success": True,
        "objects": scene_data["objects"]
    })

@app.route('/api/objects', methods=['POST'])
def add_object():
    """Ajoute un nouvel objet 3D"""
    try:
        data = request.json
        new_object = {
            "id": scene_data["last_id"] + 1,
            "name": data.get("name", f"Object_{scene_data['last_id'] + 1}"),
            "type": data.get("type", "box"),
            "position": data.get("position", {"x": 0, "y": 0, "z": 0}),
            "rotation": data.get("rotation", {"x": 0, "y": 0, "z": 0}),
            "scale": data.get("scale", {"x": 1, "y": 1, "z": 1}),
            "material": data.get("material", "steel"),
            "visible": data.get("visible", True),
            "created_at": datetime.now().isoformat()
        }
        
        scene_data["objects"].append(new_object)
        scene_data["last_id"] += 1
        
        # Ajouter à l'historique
        scene_data["history"].append({
            "action": "create",
            "object_id": new_object["id"],
            "object_name": new_object["name"],
            "timestamp": datetime.now().isoformat()
        })
        
        return jsonify({
            "success": True,
            "object": new_object
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/api/objects/<int:obj_id>', methods=['PUT'])
def update_object(obj_id):
    """Met à jour un objet existant"""
    try:
        data = request.json
        obj = find_object_by_id(obj_id)
        
        if not obj:
            return jsonify({
                "success": False,
                "error": f"Object {obj_id} not found"
            }), 404
        
        # Mettre à jour les champs
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
        
        # Ajouter à l'historique
        scene_data["history"].append({
            "action": "update",
            "object_id": obj_id,
            "object_name": obj["name"],
            "timestamp": datetime.now().isoformat()
        })
        
        return jsonify({
            "success": True,
            "object": obj
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/api/objects/<int:obj_id>', methods=['DELETE'])
def delete_object(obj_id):
    """Supprime un objet"""
    try:
        obj = find_object_by_id(obj_id)
        
        if not obj:
            return jsonify({
                "success": False,
                "error": f"Object {obj_id} not found"
            }), 404
        
        scene_data["objects"] = [o for o in scene_data["objects"] if o["id"] != obj_id]
        
        # Ajouter à l'historique
        scene_data["history"].append({
            "action": "delete",
            "object_id": obj_id,
            "object_name": obj["name"],
            "timestamp": datetime.now().isoformat()
        })
        
        return jsonify({
            "success": True,
            "message": f"Object {obj_id} deleted"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/api/sketch', methods=['POST'])
def save_sketch():
    """Sauvegarde un dessin (sketch) pour extrusion"""
    try:
        data = request.json
        sketch_data = {
            "id": datetime.now().timestamp(),
            "type": data.get("type"),
            "points": data.get("points", []),
            "params": data.get("params", {}),
            "timestamp": datetime.now().isoformat()
        }
        
        # Stocker temporairement le sketch
        if not hasattr(app, 'sketches'):
            app.sketches = []
        app.sketches.append(sketch_data)
        
        return jsonify({
            "success": True,
            "sketch_id": sketch_data["id"]
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/api/extrude', methods=['POST'])
def extrude_shape():
    """Extrude une forme 2D en 3D"""
    try:
        data = request.json
        sketch_id = data.get("sketch_id")
        depth = data.get("depth", 2.0)
        
        # Récupérer le sketch
        if not hasattr(app, 'sketches'):
            return jsonify({"success": False, "error": "No sketch found"}), 400
        
        sketch = None
        for s in app.sketches:
            if s["id"] == sketch_id:
                sketch = s
                break
        
        if not sketch:
            return jsonify({"success": False, "error": "Sketch not found"}), 404
        
        # Créer un objet 3D à partir du sketch
        new_object = {
            "id": scene_data["last_id"] + 1,
            "name": f"Extruded_{sketch['type']}_{int(sketch['id'])}",
            "type": "extrusion",
            "position": {"x": 0, "y": 0, "z": 0},
            "rotation": {"x": 0, "y": 0, "z": 0},
            "scale": {"x": 1, "y": 1, "z": 1},
            "material": data.get("material", "steel"),
            "visible": True,
            "extrude_depth": depth,
            "sketch_data": sketch,
            "created_at": datetime.now().isoformat()
        }
        
        scene_data["objects"].append(new_object)
        scene_data["last_id"] += 1
        
        # Nettoyer le sketch utilisé
        app.sketches = [s for s in app.sketches if s["id"] != sketch_id]
        
        return jsonify({
            "success": True,
            "object": new_object
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/api/export/stl', methods=['POST'])
def export_stl():
    """Exporte la scène au format STL"""
    try:
        data = request.json
        objects_to_export = data.get("objects", scene_data["objects"])
        
        # Générer le contenu STL
        stl_content = generate_stl(objects_to_export)
        
        # Sauvegarder dans un fichier temporaire
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.stl"
        filepath = os.path.join(TEMP_DIR, filename)
        
        with open(filepath, 'w') as f:
            f.write(stl_content)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/api/export/obj', methods=['POST'])
def export_obj():
    """Exporte la scène au format OBJ"""
    try:
        data = request.json
        objects_to_export = data.get("objects", scene_data["objects"])
        
        # Générer le contenu OBJ
        obj_content = generate_obj(objects_to_export)
        
        # Sauvegarder dans un fichier temporaire
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.obj"
        filepath = os.path.join(TEMP_DIR, filename)
        
        with open(filepath, 'w') as f:
            f.write(obj_content)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/api/history', methods=['GET'])
def get_history():
    """Récupère l'historique des actions"""
    return jsonify({
        "success": True,
        "history": scene_data["history"]
    })

@app.route('/api/history/clear', methods=['DELETE'])
def clear_history():
    """Efface l'historique"""
    scene_data["history"] = []
    return jsonify({
        "success": True,
        "message": "History cleared"
    })

@app.route('/api/undo', methods=['POST'])
def undo_action():
    """Annule la dernière action"""
    # Implémentation simplifiée - dans la réalité, il faudrait un vrai système d'undo
    if scene_data["history"]:
        last_action = scene_data["history"].pop()
        return jsonify({
            "success": True,
            "undone_action": last_action
        })
    return jsonify({
        "success": False,
        "error": "Nothing to undo"
    }), 400

@app.route('/api/clear', methods=['DELETE'])
def clear_scene():
    """Efface toute la scène"""
    scene_data["objects"] = []
    scene_data["history"].append({
        "action": "clear_all",
        "timestamp": datetime.now().isoformat()
    })
    return jsonify({
        "success": True,
        "message": "Scene cleared"
    })

# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def find_object_by_id(obj_id):
    """Trouve un objet par son ID"""
    for obj in scene_data["objects"]:
        if obj["id"] == obj_id:
            return obj
    return None

def generate_stl(objects):
    """Génère le contenu STL à partir des objets"""
    stl = "solid CAD_Studio_Export\n"
    
    for obj in objects:
        stl += f"  facet normal 0 1 0\n"
        stl += f"    outer loop\n"
        
        # Générer des sommets simplifiés pour la démonstration
        pos = obj.get("position", {"x": 0, "y": 0, "z": 0})
        scale = obj.get("scale", {"x": 1, "y": 1, "z": 1})
        
        # Cube simplifié pour l'export
        x, y, z = pos["x"], pos["y"], pos["z"]
        sx, sy, sz = scale["x"], scale["y"], scale["z"]
        
        vertices = [
            (x-sx, y-sy, z-sz), (x+sx, y-sy, z-sz),
            (x+sx, y+sy, z-sz), (x-sx, y+sy, z-sz),
            (x-sx, y-sy, z+sz), (x+sx, y-sy, z+sz),
            (x+sx, y+sy, z+sz), (x-sx, y+sy, z+sz)
        ]
        
        # Écrire les faces du cube
        faces = [
            [0,1,2], [0,2,3],  # Face avant
            [4,6,5], [4,7,6],  # Face arrière
            [0,4,5], [0,5,1],  # Face basse
            [2,6,7], [2,7,3],  # Face haute
            [0,3,7], [0,7,4],  # Face gauche
            [1,5,6], [1,6,2]   # Face droite
        ]
        
        for face in faces:
            stl += f"      vertex {vertices[face[0]][0]} {vertices[face[0]][1]} {vertices[face[0]][2]}\n"
            stl += f"      vertex {vertices[face[1]][0]} {vertices[face[1]][1]} {vertices[face[1]][2]}\n"
            stl += f"      vertex {vertices[face[2]][0]} {vertices[face[2]][1]} {vertices[face[2]][2]}\n"
        stl += f"    endloop\n"
        stl += f"  endfacet\n"
    
    stl += "endsolid CAD_Studio_Export\n"
    return stl

def generate_obj(objects):
    """Génère le contenu OBJ à partir des objets"""
    obj = f"# CAD Studio Pro Export\n# Generated: {datetime.now().isoformat()}\n\n"
    
    vertex_offset = 1
    
    for idx, obj_data in enumerate(objects):
        obj += f"o {obj_data.get('name', f'Object_{idx}')}\n"
        
        pos = obj_data.get("position", {"x": 0, "y": 0, "z": 0})
        scale = obj_data.get("scale", {"x": 1, "y": 1, "z": 1})
        
        # Sommets du cube
        x, y, z = pos["x"], pos["y"], pos["z"]
        sx, sy, sz = scale["x"], scale["y"], scale["z"]
        
        vertices = [
            (x-sx, y-sy, z-sz), (x+sx, y-sy, z-sz),
            (x+sx, y+sy, z-sz), (x-sx, y+sy, z-sz),
            (x-sx, y-sy, z+sz), (x+sx, y-sy, z+sz),
            (x+sx, y+sy, z+sz), (x-sx, y+sy, z+sz)
        ]
        
        for v in vertices:
            obj += f"v {v[0]} {v[1]} {v[2]}\n"
        
        obj += "\n"
        
        # Faces
        faces = [
            [1,2,3], [1,3,4],  # Face avant
            [5,7,6], [5,8,7],  # Face arrière
            [1,5,6], [1,6,2],  # Face basse
            [3,7,8], [3,8,4],  # Face haute
            [1,4,8], [1,8,5],  # Face gauche
            [2,6,7], [2,7,3]   # Face droite
        ]
        
        for face in faces:
            obj += f"f {face[0]+vertex_offset-1} {face[1]+vertex_offset-1} {face[2]+vertex_offset-1}\n"
        
        obj += "\n"
        vertex_offset += 8
    
    return obj

# ============================================================
# NETTOYAGE DES FICHIERS TEMPORAIRES
# ============================================================

def cleanup_temp_files():
    """Nettoie les fichiers temporaires"""
    import shutil
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

# ============================================================
# LANCEMENT DE L'APPLICATION
# ============================================================

if __name__ == '__main__':
    try:
        print("=" * 50)
        print("CAD EDITOR - SERVEUR FLASK")
        print("=" * 50)
        print(f"Dossier temporaire: {TEMP_DIR}")
        print("\n📌 Accédez à l'éditeur CAD sur:")
        print("   http://localhost:5000")
        print("\n📌 Commandes disponibles:")
        print("   - GET  /api/objects      → Liste des objets")
        print("   - POST /api/objects      → Ajouter un objet")
        print("   - PUT  /api/objects/<id> → Modifier un objet")
        print("   - DEL  /api/objects/<id> → Supprimer un objet")
        print("   - POST /api/extrude      → Extruder un sketch")
        print("   - POST /api/export/stl   → Exporter STL")
        print("   - POST /api/export/obj   → Exporter OBJ")
        print("\n🚀 Démarrage du serveur...")
        print("-" * 50)
        
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du serveur...")
        cleanup_temp_files()
        print("✅ Nettoyage terminé")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        cleanup_temp_files()
