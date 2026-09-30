exec(compile((__import__('pathlib').Path(__file__).resolve().parent/'verify-timing-native.py').read_text().split('hits=[]')[0],__file__,'exec'))
scene.frame_set(37,subframe=2/3)
a,b=gears['fuel11'],gears['fuel21'];hits=tree(a).overlap(tree(b))
for o,index in [(a,i) for i,j in hits]+[(b,j) for i,j in hits]:
 t=o.data.loop_triangles[index];vs=[root.matrix_world.inverted()@o.matrix_world@o.data.vertices[i].co for i in t.vertices]
 apex=C(timing['gears'][o['timingGearId']]['origin']);print(o.name,index,'radii',[(v-apex).length for v in vs],'verts',[tuple(v) for v in vs],flush=True)
