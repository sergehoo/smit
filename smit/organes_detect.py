import torch
import torchvision.transforms as T
from PIL import Image
import numpy as np
import pydicom
import torchxrayvision as xrv
from skimage.measure import label, regionprops

# --- Segmentation poumons (TorchXRayVision) ---
# modèle UNet pré-entraîné pour segmenter les poumons

from torchvision.models import resnet50, ResNet50_Weights
resnet_weights = ResNet50_Weights.DEFAULT
classification_model = resnet50(weights=resnet_weights).eval()
transform_cls = resnet_weights.transforms()


def _load_image_any(path: str) -> Image.Image:
    """Charge PNG/JPG ou DICOM en PIL RGB."""
    if path.lower().endswith((".dcm", ".dicom")):
        dcm = pydicom.dcmread(path)
        arr = dcm.pixel_array.astype(np.float32)
        # normalisation simple en 0..255
        arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-8)
        arr = (arr * 255.0).clip(0, 255).astype(np.uint8)
        pil = Image.fromarray(arr)
        return pil.convert("RGB")
    else:
        return Image.open(path).convert("RGB")


def _boxes_from_mask(mask: np.ndarray):
    """Calcule des boîtes englobantes par composante connexe."""
    # mask bool -> label regions
    lab = label(mask > 0)
    boxes = []
    for r in regionprops(lab):
        y1, x1, y2, x2 = r.bbox  # (min_row, min_col, max_row, max_col)
        boxes.append([float(x1), float(y1), float(x2), float(y2)])
    return boxes


def detecter_organes_rxt(path: str):
    """
    Détection stricte d’organes pour radio thoracique :
    - Segmente les poumons (gauche/droite) avec TorchXRayVision
    - Retourne boxes + labels + noms
    """
    pil = _load_image_any(path)
    w, h = pil.size
    # TorchXRayVision attend une image normalisée [0,1] en Tensor [1,1,H,W]
    img_gray = pil.convert("L")
    arr = np.asarray(img_gray).astype(np.float32) / 255.0
    ten = torch.from_numpy(arr[None, None, ...]).to(device)

    with torch.inference_mode():
        # sortie: masque [1,1,H,W] (poumons)
        mask = lung_seg_model(ten)  # logits
        mask = (torch.sigmoid(mask) > 0.5).float().cpu().numpy()[0, 0]

    boxes = _boxes_from_mask(mask)
    labels = []
    names = []
    scores = []

    if len(boxes) > 0:
        # On considère 2 poumons (gauche/droite) si deux composantes,
        # sinon on renvoie "Lungs" en un seul bloc
        if len(boxes) == 2:
            labels = [1, 2]  # 1: Left lung, 2: Right lung (convention locale)
            names = ["Left lung", "Right lung"]
            scores = [1.0, 1.0]
        else:
            labels = [0]
            names = ["Lungs"]
            scores = [1.0]

    return {
        "image_size": [w, h],
        "boxes": boxes,  # [x1,y1,x2,y2] en pixels
        "labels": labels,  # ids locaux
        "names": names,  # noms anatomiques
        "scores": scores,  # confiance (1.0 car binaire)
        "seuil": 0.5,
    }


# Base des catégories médicales fictives (à remplacer par des classes réelles)
CATEGORIES_MEDICALES = {
    0: "Image normale - Aucun signe anormal",
    1: "Opacité pulmonaire suspecte - Vérification d'une infection ou inflammation",
    2: "Fracture osseuse détectée - Vérifier l'intégrité osseuse",
    3: "Masse anormale détectée - Analyse approfondie nécessaire",
    4: "Calcification suspecte - Vérification des tissus calcifiés",
    5: "Lésion possible - Demander confirmation du radiologue"
}

ORGANES_DETECTES = {
    # Respiratory System
    1: "Lung",
    2: "Bronchi",
    3: "Trachea",
    4: "Diaphragm",

    # Cardiovascular System
    5: "Heart",
    6: "Aorta",
    7: "Superior vena cava",
    8: "Inferior vena cava",
    9: "Coronary arteries",

    # Digestive System
    10: "Liver",
    11: "Gallbladder",
    12: "Pancreas",
    13: "Stomach",
    14: "Small intestine",
    15: "Colon",
    16: "Rectum",
    17: "Esophagus",

    # Urinary System
    18: "Kidneys",
    19: "Ureters",
    20: "Bladder",
    21: "Urethra",

    # Nervous System
    22: "Encephalon",
    23: "Brain",
    24: "Cerebellum",
    25: "Brainstem",
    26: "Spinal cord",

    # Musculoskeletal System
    27: "Spinal column",
    28: "Cervical vertebrae",
    29: "Thoracic vertebrae",
    30: "Lumbar vertebrae",
    31: "Sacrum",
    32: "Coccyx",
    33: "Skull",
    34: "Mandible",
    35: "Clavicle",
    36: "Scapula",
    37: "Humerus",
    38: "Radius",
    39: "Ulna",
    40: "Carpals (Wrist)",
    41: "Metacarpals",
    42: "Phalanges (Fingers)",
    43: "Femur",
    44: "Patella",
    45: "Tibia",
    46: "Fibula",
    47: "Tarsals (Ankle)",
    48: "Metatarsals",
    49: "Phalanges (Toes)",

    # Male Reproductive System
    50: "Testicles",
    51: "Epididymis",
    52: "Vas deferens",
    53: "Prostate",
    54: "Seminal vesicles",
    55: "Penis",

    # Female Reproductive System
    56: "Ovaries",
    57: "Fallopian tubes",
    58: "Uterus",
    59: "Cervix",
    60: "Vagina",
    61: "Mammary glands (Breasts)",

    # Endocrine System
    62: "Pituitary gland",
    63: "Thyroid gland",
    64: "Parathyroid glands",
    65: "Adrenal glands",

    # Lymphatic System
    66: "Lymph nodes",
    67: "Spleen",
    68: "Bone marrow",
    69: "Thymus",

    # Sensory System
    70: "Eyeball",
    71: "Retina",
    72: "Lens",
    73: "Optic nerve",
    74: "Inner ear",
    75: "Middle ear",
    76: "Outer ear",
    77: "Nose",
    78: "Tongue",

    # Major Joints
    79: "Shoulder",
    80: "Elbow",
    81: "Wrist",
    82: "Hip",
    83: "Knee",
    84: "Ankle",
}


# Hypothèses :
# - classification_model et detection_model sont déjà chargés, en .eval(), sur le bon device
# - transform est le preprocessing adapté au modèle de classification (même normalisation que ses weights)
# - ORGANES_DETECTES et CATEGORIES_MEDICALES sont des dicts existants
# - Pour Torchvision >= 0.13, préférer weights=... pour connaître la normalisation attendue

def analyser_image(image_path: str):
    try:
        pil = _load_image_any(image_path)

        # --- CLASSIFICATION (facultative) ---
        with torch.inference_mode():
            img_cls = transform_cls(pil).unsqueeze(0).to(device, non_blocking=True)
            logits = classification_model(img_cls)
            probs = torch.softmax(logits, dim=1)
            pred = int(torch.argmax(probs, dim=1))
            proba = float(probs[0, pred]) * 100.0
        cat = CATEGORIES_MEDICALES.get(pred, "Analyse indéterminée")
        if proba < 20:
            niveau = "🟢 Normal"
        elif proba < 50:
            niveau = "🟡 Suspect - Vérification conseillée"
        elif proba < 80:
            niveau = "🟠 Alerte - Examen approfondi recommandé"
        else:
            niveau = "🔴 Critique - Intervention médicale urgente"

        # --- ORGANES (poumons) ---
        det = detecter_organes_rxt(image_path)
        organes = det["names"] if det["names"] else ["Non identifié"]

        return {
            "prediction": pred,
            "probabilite": round(proba, 2),
            "categorie": cat,
            "niveau_risque": niveau,
            "organes_detectes": organes,
            "detection": det,
        }
    except Exception as e:
        return {
            "error": str(e),
            "prediction": None,
            "probabilite": None,
            "categorie": "Erreur d'analyse",
            "niveau_risque": "Indisponible",
            "organes_detectes": [],
            "detection": {},
        }
