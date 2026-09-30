import * as T from 'three';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';
export async function exportGLB(root, originalMaterials, animations = []) {
    const scene = new T.Scene();
    scene.name = 'MAZ543_REFERENCE';
    const copy = root.clone(true);
    scene.add(copy);
    const materials = new Map();
    copy.traverse(o => {
        if (!(o instanceof T.Mesh))
            return;
        const src = originalMaterials.get(o.name) || o.material;
        if (!materials.has(src)) {
            const mat = src.clone();
            mat.clippingPlanes = null;
            mat.wireframe = false;
            mat.map = null;
            mat.bumpMap = null;
            mat.roughnessMap = null;
            materials.set(src, mat);
        }
        o.material = materials.get(src);
    });
    try {
        return await new GLTFExporter().parseAsync(scene, { binary: true, onlyVisible: true, animations });
    }
    finally {
        materials.forEach(mat => mat.dispose());
    }
}
