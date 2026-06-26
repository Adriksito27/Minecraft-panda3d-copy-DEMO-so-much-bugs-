from math import pi, sin, cos
from direct.showbase.ShowBase import ShowBase
from panda3d.core import loadPrcFile, CullFaceAttrib
from panda3d.core import DirectionalLight, AmbientLight, BitMask32, TextNode
from panda3d.core import TransparencyAttrib
from panda3d.core import WindowProperties
from panda3d.core import CollisionTraverser, CollisionNode, CollisionBox, CollisionRay, CollisionHandlerQueue, CollisionHandlerPusher, CollisionCapsule
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import ClockObject
from noise import pnoise2
from direct.gui.DirectButton import DirectButton
import random

loadPrcFile('settings.prc')

def degToRad(degrees):
    return degrees * (pi / 180.0)

class MyGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.seed_x = random.randint(0, 100000)
        self.seed_y = random.randint(0, 100000)
        self.hotbarSlots = ['grass', 'dirt', 'sand', 'stone', 'wood']
        self.pusher = CollisionHandlerPusher()
        self.selectedBlockType = 'grass'
        self.globalClock = ClockObject.getGlobalClock
        self.loadModels()
        self.setupLights()
        self.generateChunk()
        self.setupFog()
        self.setFrameRateMeter(True)
        self.camera.setPos(-10, 16, 16) 
        self.setBackgroundColor(0.47, 0.65, 1.0)
        self.setupCamera()
        self.captureMouse()
        self.setupControls()
        self.setupInventoryUI()
        self.taskMgr.add(self.update, 'update')
        self.globalClock = ClockObject.getGlobalClock()
        self.customFont = self.loader.loadFont('Minecraft.ttf')
        self.blockText = OnscreenText(
            text="Grass", 
            pos=(0, -0.75),                  
            scale=0.07,                        
            fg=(1, 1, 1, 1),
            shadow=(0, 0, 0, 0.8),
            font=self.customFont,                            
            align=TextNode.ACenter,                            
            mayChange=True
        )
        self.render.setTwoSided(False)
        self.updateHandBlock()
    




    def update(self, task):
        
        dt = self.globalClock.getDt()
        playerMoveSpeed = 5

        x_movement = 0
        y_movement = 0
        
        z_movement = 0

        if self.cameraSwingActivated:
            if self.keyMap['forward']:
                x_movement -= dt * playerMoveSpeed * sin(degToRad(self.camera.getH()))
                y_movement += dt * playerMoveSpeed * cos(degToRad(self.camera.getH()))
            if self.keyMap['backward']:
                x_movement += dt * playerMoveSpeed * sin(degToRad(self.camera.getH()))
                y_movement -= dt * playerMoveSpeed * cos(degToRad(self.camera.getH()))
            if self.keyMap['left']:
                x_movement -= dt * playerMoveSpeed * cos(degToRad(self.camera.getH()))
                y_movement -= dt * playerMoveSpeed * sin(degToRad(self.camera.getH()))
            if self.keyMap['right']:
                x_movement += dt * playerMoveSpeed * cos(degToRad(self.camera.getH()))
                y_movement += dt * playerMoveSpeed * sin(degToRad(self.camera.getH()))
            if self.keyMap['up']:
                z_movement += dt * playerMoveSpeed
            if self.keyMap['down']:
                z_movement -= dt * playerMoveSpeed    
        
        self.camera.setPos(
            self.camera.getX() + x_movement,
            self.camera.getY() + y_movement,
            self.camera.getZ() + z_movement
        )
        
        if self.cameraSwingActivated:
            md = self.win.getPointer(0)
            mouseX = md.getX()
            mouseY = md.getY()

            mouseChangeX = mouseX - self.lastMouseX
            mouseChangeY = mouseY - self.lastMouseY

            self.cameraSwingFactor = 10
            currentH = self.camera.getH()
            currentP = self.camera.getP()

            self.camera.setHpr(
                currentH - mouseChangeX * dt * self.cameraSwingFactor,
                min(90, max(-90, currentP - mouseChangeY * dt * self.cameraSwingFactor)),
                0
            )

            self.lastMouseX = mouseX
            self.lastMouseY = mouseY
        
        return task.cont

    def setSelectedBlockType(self, type):
        self.selectedBlockType = type
        self.blockText.setText(f"{type.capitalize()}")
    
    def updateHandBlock(self):
        if hasattr(self, 'hand_block') and self.hand_block:
            self.hand_block.removeNode()
       
        block_name = (self.selectedBlockType)

        self.hand_block = self.loader.loadModel(f"{block_name}-block.glb")
        
       
        self.hand_block.reparentTo(self.camera)
        self.hand_block.setTransparency(TransparencyAttrib.MAlpha)
        self.hand_block.setBin('transparent', 0)
        self.hand_block.setDepthOffset(-1)
            
       
        self.hand_block.setPos(1.2, 2.5, -0.8)
        self.hand_block.setHpr(-15, 10, 5) 
        self.hand_block.setScale(0.4)
        
       
        self.hand_block.setCollideMask(0)

    def generateTree(self, tx, ty, base_z):
        # Altura aleatoria para el tronco (entre 4 y 6 bloques)
        trunk_height = random.randint(4, 6)
        
        # 1. Crear el tronco de madera
        for z in range(base_z, base_z + trunk_height):
            self.world_data[(tx, ty, z)] = 'wood'
            
        # 2. Crear las hojas (Copa del árbol)
        leaves_start_z = base_z + trunk_height - 2
        for lz in range(leaves_start_z, leaves_start_z + 3):
            # Las capas de abajo son más anchas (radio 2), la de arriba es más pequeña (radio 1)
            radius = 2 if lz < leaves_start_z + 2 else 1
            
            for lx in range(tx - radius, tx + radius + 1):
                for ly in range(ty - radius, ty + radius + 1):
                    # Evitar poner hojas fuera de los límites de la matriz si es necesario
                    if 0 <= lx < 16 and 0 <= ly < 16:
                        # No sobrescribir el tronco central con hojas
                        if (lx == tx and ly == ty and lz < base_z + trunk_height):
                            continue
                        # Probabilidad pequeña de omitir esquinas para que sea más redondo
                        if radius == 2 and (abs(lx - tx) == 2 and abs(ly - ty) == 2) and random.random() < 0.5:
                            continue
                        
                        self.world_data[(lx, ly, lz)] = 'leaves'



    def handleLeftClick(self):
        self.removeBlock()
        self.captureMouse()

    def setupInventoryUI(self):
        self.hotbarBg = OnscreenImage(image='Hotbar.png',
                                      pos= (0, 0, -0.85),
                                      scale=(0.6, 1, 0.08))
        self.hotbarBg.setTransparency(TransparencyAttrib.MAlpha)
        self.selector_ui = OnscreenImage(image='Hotbar_selector.png',
                                         pos=(-0.5241, 0, -0.85),
                                         scale=(0.08, 1, 0.08))
        self.selector_ui.setTransparency(TransparencyAttrib.MAlpha)

        self.hotbarItems = ['grass', 'dirt', 'sand', 'stone', 'wood', 'planks', 'leaves', 'glass', 'cobblestone']
        self.itemIcons = {
            'grass': 'grass.png',
            'dirt': 'dirt.png',
            'sand': 'sand.png',
            'stone': 'stone.png',
            'wood': 'wood.png',
            'planks': 'planks.png',
            'leaves': 'leaves.png',
            'glass': 'glass.png',
            'cobblestone': 'cobblestone.png'
        }
        self.itemImagesUI = []

        for slot_index, item_name in enumerate(self.hotbarItems):
            if item_name != "":
                x = -0.5241 + (slot_index * 0.131)

                icon = OnscreenImage(
                    image=self.itemIcons[item_name],
                    pos=(x, 0, -0.85), # Misma altura z que la barra
                    scale=(0.045, 1, 0.045) # Un poco mas pequeño que la casilla para que quepa dentro
                )
                icon.setTransparency(TransparencyAttrib.MAlpha)
                self.itemImagesUI.append(icon)
        
        


    def selectSlot(self, slotIndex):
        newXPos = -0.5241 + (slotIndex * 0.133)
        self.selector_ui.setX(newXPos)
        self.current_block_type = self.hotbarSlots[slotIndex]

    def removeBlock(self):
        if not self.cameraSwingFactor: return
        self.cTrav.traverse(self.render) 

        if self.rayQueue.getNumEntries() > 0:
            self.rayQueue.sortEntries()
            rayHit = self.rayQueue.getEntry(0)
            
            hitCollider = rayHit.getIntoNodePath()
            hitObject = hitCollider.getPythonTag('owner') 
            
            if hitObject:
                distanceFromPlayer = hitObject.getDistance(self.camera)
                if distanceFromPlayer < 40: 
                    hitCollider.clearPythonTag('owner')
                    hitObject.removeNode()
                    hitCollider.removeNode()

    def placeBlock(self):
        self.cTrav.traverse(self.render)

        if self.rayQueue.getNumEntries() > 0:
            self.rayQueue.sortEntries()
            rayHit = self.rayQueue.getEntry(0)
            
            hitCollider = rayHit.getIntoNodePath()
            normal = rayHit.getSurfaceNormal(self.render) 
            hitObject = hitCollider.getPythonTag('owner')

            if hitObject:
                distanceFromPlayer = hitObject.getDistance(self.camera)
                if distanceFromPlayer < 40:
                    hitBlockPos = hitObject.getPos()
                    newBlockPos = hitBlockPos + normal * 2 
                    self.createNewBlock(newBlockPos.x, newBlockPos.y, newBlockPos.z, self.selectedBlockType)
    
    def updateKeyMap(self, key, value):

        if self.cameraSwingFactor:
            self.keyMap[key] = value
        else:
            self.keyMap[key] = False

    def setupControls(self):
        self.keyMap = {
            "forward": False,
            "backward": False,
            "left": False,
            "right": False,
            "up": False,
            "down": False,
        }

        self.accept('escape', self.releaseMouse)
        self.accept('mouse1', self.handleLeftClick)
        self.accept('mouse3', self.placeBlock)

        self.accept('w', self.updateKeyMap, ['forward', True])
        self.accept('w-up', self.updateKeyMap, ['forward', False])
        self.accept('a', self.updateKeyMap, ['left', True])
        self.accept('a-up', self.updateKeyMap, ['left', False])
        self.accept('s', self.updateKeyMap, ['backward', True])
        self.accept('s-up', self.updateKeyMap, ['backward', False])
        self.accept('d', self.updateKeyMap, ['right', True])
        self.accept('d-up', self.updateKeyMap, ['right', False])
        self.accept('space', self.updateKeyMap, ['up', True])
        self.accept('space-up', self.updateKeyMap, ['up', False])
        self.accept('lshift', self.updateKeyMap, ['down', True])
        self.accept('lshift-up', self.updateKeyMap, ['down', False])

        self.accept('1', self.changeItem, ['grass', 0])
        self.accept('2', self.changeItem, ['dirt', 1])
        self.accept('3', self.changeItem, ['sand', 2])
        self.accept('4', self.changeItem, ['stone', 3])
        self.accept('5', self.changeItem, ['wood', 4])
        self.accept('6', self.changeItem, ['planks', 5])
        self.accept('7', self.changeItem, ['leaves', 6])
        self.accept('8', self.changeItem, ['glass', 7])
        self.accept('9', self.changeItem, ['cobblestone', 8])
            
    
                    
    def changeItem(self, blockId, slotIndex):
        self.setSelectedBlockType(blockId)
        
        self.selected_slot = slotIndex 
        
        newXpos = -0.53 + (slotIndex * 0.133)
        self.selector_ui.setX(newXpos)   
        self.updateHandBlock() 

    def captureMouse(self):
        self.cameraSwingActivated = True
        md = self.win.getPointer(0)
        self.lastMouseX = md.getX()
        self.lastMouseY = md.getY()

        properties = WindowProperties()
        properties.setCursorHidden(True)
        properties.setMouseMode(WindowProperties.M_relative)
        self.win.requestProperties(properties)

    def releaseMouse(self):
        self.cameraSwingActivated = False
        properties = WindowProperties()
        properties.setCursorHidden(False)
        properties.setMouseMode(WindowProperties.M_absolute)
        self.win.requestProperties(properties)

    def setupFog(self):
        from panda3d.core import Fog
        
        self.gameFog = Fog("SkyFog")
        
        fogColor = (0.47, 0.65, 1.0) 
        self.gameFog.setColor(*fogColor)
       
        self.gameFog.setLinearRange(50.0, 70.0)
        

        self.render.setFog(self.gameFog)

    def setupCamera(self):
        self.disableMouse()
        self.camLens.setFov(80)
        self.camLens.setNear(0.1)
        self.camLens.setFar(100)

        crosshairs = OnscreenImage(
            image = 'crosshairs.png',
            pos = (0, 0, 0),
            scale = 0.05,
        )
        crosshairs.setTransparency(TransparencyAttrib.MAlpha)

        # --- AJUSTE PARA BLOQUES DE TAMAÑO 2 ---
        # Ancho original 0.9 bloques -> 0.9 * 2 = 1.8 unidades totales (Radio = 0.9)
        radius = 0.9
        
        # Altura original 1.9 bloques -> 1.9 * 2 = 3.8 unidades totales desde el suelo
        # La cámara (los ojos) se sitúa a ~3.24 unidades del suelo (proporcional a tus bloques de 2)
        bottom_z = -3.24 + radius        # Punto inferior de la cápsula
        top_z = (-3.24 + 3.8) - radius   # Punto superior de la cápsula
        
        playerCapsule = CollisionCapsule(0, 0, bottom_z, 0, 0, top_z, radius)
        
        playerNode = CollisionNode('player-collider')
        playerNode.addSolid(playerCapsule)
        playerNode.setFromCollideMask(BitMask32.bit(1))
        playerNode.setIntoCollideMask(0)
        playerNodePath = self.camera.attachNewNode(playerNode)
        
        # Descomenta esto para ver la cápsula azul de debug en el juego si lo necesitas:
        # playerNodePath.show()
        # --------------------------------------------------------

        self.pusher.addCollider(playerNodePath, self.camera)

        self.cTrav = CollisionTraverser()
        self.cTrav.addCollider(playerNodePath, self.pusher)
        
        ray = CollisionRay()
        ray.setFromLens(self.camNode, (0, 0))
        rayNode = CollisionNode('line-of-sight')
        rayNode.addSolid(ray)
        rayNode.setFromCollideMask(BitMask32.bit(2)) 
        rayNode.setIntoCollideMask(0)
        
        rayNodePath = self.camera.attachNewNode(rayNode)
        self.rayQueue = CollisionHandlerQueue()
        self.cTrav.addCollider(rayNodePath, self.rayQueue)

    def generateChunk(self):
        self.world_data = {}

        noiseScale = 0.167
        minHeight = 7
        maxHeight = 6


        for x in range(16):
            for y in range(16):
                noise = pnoise2(
                    (x + self.seed_x) * noiseScale, 
                    (y + self.seed_y) * noiseScale, 
                    octaves=2, 
                    persistence=0.5
                )

                finalHeight = int(minHeight + ((noise + 1) / 2) * maxHeight)
                finalHeight = max(1, min(finalHeight, 14))

                for z in range(finalHeight):
                    if z == finalHeight - 1:
                        block_type = 'grass'
                    elif z >= finalHeight - 3:
                        block_type = 'dirt'
                    else:
                        block_type = 'stone'

                    self.world_data[(x, y, z)] = block_type


                if 2 <= x < 14 and 2 <= y < 14:
                    if random.random() < 0.04: 
                        too_close = False
                        for check_x in range(x - 3, x + 4):
                            for check_y in range(y - 3, y + 4):
                                
                                if any(self.world_data.get((check_x, check_y, check_z)) == 'wood' for check_z in range(16)):
                                    too_close = True
                                    break
                            if too_close:
                                break

                        if not too_close:
                            self.generateTree(x, y, finalHeight)    

        for (x, y, z), block_type in self.world_data.items():
            real_x = x * 2 - 16
            real_y = y * 2 - 16
            real_z = z * 2
            
            self.createNewBlock(real_x, real_y, real_z, block_type, needsCollision=True)
           
            
        
    def createNewBlock(self, x, y, z, type, needsCollision = True):
        self.newBlockNode = self.render.attachNewNode('new-block-placeholder')
        self.newBlockNode.setPos(x, y, z)

        if type == 'grass':
            self.grassBlock.instanceTo(self.newBlockNode)
        elif type == 'dirt':
            self.dirtBlock.instanceTo(self.newBlockNode)
        elif type == 'sand':
            self.sandBlock.instanceTo(self.newBlockNode)
        elif type == 'stone':
            self.stoneBlock.instanceTo(self.newBlockNode)
        elif type == 'wood':
            self.woodLog.instanceTo(self.newBlockNode)
        elif type == 'planks':
            self.woodPlanks.instanceTo(self.newBlockNode)
        elif type == 'leaves':
            self.leavesBlock.instanceTo(self.newBlockNode)
            self.newBlockNode.setTransparency(TransparencyAttrib.MAlpha)
            self.newBlockNode.setBin('transparent', 0)
            self.newBlockNode.setDepthOffset(-1)
        elif type == 'glass':
            self.glassBlock.instanceTo(self.newBlockNode)
            self.newBlockNode.setTransparency(TransparencyAttrib.MAlpha)
            self.newBlockNode.setBin('transparent', 0)
            self.newBlockNode.setDepthOffset(-1)
        elif type == 'cobblestone':
            self.cobbleBlock.instanceTo(self.newBlockNode)
        

        if type != '':
            self.blockSolid = CollisionBox((x, y, z), 1, 1, 1)
            self.blockNode = CollisionNode('block-collision-node')
            self.blockNode.addSolid(self.blockSolid)
            self.blockNode.setIntoCollideMask(BitMask32.bit(1) | BitMask32.bit(2)) 
        
        # Adjuntamos el colisionador directamente al render para independizar las coordenadas globales
        collider = self.render.attachNewNode(self.blockNode)
        collider.setPythonTag('owner', self.newBlockNode)

    def loadModels(self):
        self.grassBlock = self.loader.loadModel('grass-block.glb')
        self.dirtBlock = self.loader.loadModel('dirt-block.glb')
        self.stoneBlock = self.loader.loadModel('stone-block.glb')
        self.sandBlock = self.loader.loadModel('sand-block.glb')
        self.woodLog = self.loader.loadModel('wood-block.glb')
        self.woodPlanks = self.loader.loadModel('planks-block.glb')
        self.leavesBlock = self.loader.loadModel('leaves-block.glb')
        self.glassBlock = self.loader.loadModel('glass-block.glb')
        self.cobbleBlock = self.loader.loadModel('cobblestone-block.glb')

    def setupLights(self):
        mainLight = DirectionalLight('main light')
        mainLightNodePath = self.render.attachNewNode(mainLight)
        mainLightNodePath.setHpr(30, -60, 0)
        self.render.setLight(mainLightNodePath)

        ambientLight = AmbientLight('ambient light')
        ambientLight.setColor((0.3, 0.3, 0.3, 1))
        ambientLightNodePath = self.render.attachNewNode(ambientLight)
        self.render.setLight(ambientLightNodePath)

game = MyGame()
game.run()