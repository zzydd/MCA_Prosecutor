"""
Create empty chunk
"""
from typing import List
from . import nbt
from .biome import Biome
from .block import Block
from .empty_section import EmptySection
from .errors import OutOfBoundsCoordinates, EmptySectionAlreadyExists

# WORLD_VERSION = 2844 # 21w43a Minecraft 1.18 snapshot 7

# 已支持任意高度的存档，用不到你了，滚吧
# NUM_SECTIONS_PER_CHUNK = 24

class EmptyChunk:
    """
    Used for making own chunks

    Attributes
    ----------
    x: :class:`int`
        Chunk's X position
    z: :class:`int`
        Chunk's Z position
    sections: List[:class:`anvil.EmptySection`]
        List of all the sections in this chunk
    version: :class:`int`
        Chunk's DataVersion
    """

    __slots__ = ('x', 'z', 'sections', 'version', 'status', 'data', 'tile_entities', 'entities')

    def __init__(self, x:int, z:int, version:int=2844, status:str="full", data=None):
        self.x = x
        self.z = z
        self.data = data
        self.status = status
        self.version = version
        #解除高度限制
        #self.sections: List[Union[EmptySection,None]] = [None] * NUM_SECTIONS_PER_CHUNK
        self.sections: dict[int, EmptySection] = {}
        self.entities = None
        self.tile_entities = None

    def add_section(self, section: EmptySection, replace: bool = True):
        """
        Adds a section to the chunk

        Parameters
        ----------
        section
            Section to add
        replace
            Whether to replace section if one at same Y already exists
        
        Raises
        ------
        anvil.EmptySectionAlreadyExists
            If ``replace`` is ``False`` and section with same Y already exists in this chunk
        """
        # 原版本
        # if section.y < -4 or section.y + 4 > NUM_SECTIONS_PER_CHUNK:
        #     raise OutOfBoundsCoordinates('section Y is too high.')
        # if self.sections[section.y + 4] and not replace:
        #     raise EmptySectionAlreadyExists(f'EmptySection (Y={section.y}) already exists in this chunk')
        # self.sections[section.y + 4] = section

        # 解除高度限制版
        y = section.y
        if y in self.sections and not replace:
            raise EmptySectionAlreadyExists(f'EmptySection (Y={y}) already exists')
        self.sections[y] = section

    def get_block(self, x: int, y: int, z: int) -> Block:
        """
        Gets the block at given coordinates
        
        Parameters
        ----------
        int x, z
            In range of 0 to 15
        y
            In range of -64 to 319

        Raises
        ------
        anvil.OutOfBoundCoordidnates
            If X, Y or Z are not in the proper range

        Returns
        -------
        block : :class:`anvil.Block` or None
            Returns ``None`` if the section is empty, meaning the block
            is most likely an air block.
        """
        if x < 0 or x > 15:
            raise OutOfBoundsCoordinates(f'X ({x!r}) must be in range of 0 to 15')
        if z < 0 or z > 15:
            raise OutOfBoundsCoordinates(f'Z ({z!r}) must be in range of 0 to 15')
        if y < -64 or y > 319:
            raise OutOfBoundsCoordinates(f'Y ({y!r}) must be in range of 0 to 255')
        section = self.sections[ (y + 64) // 16]
        if section is None:
            return None
        return section.get_block(x, y % 16, z)

    def set_block(self, block: Block, x: int, y: int, z: int):
        """
        Sets block at given coordinates
        
        Parameters
        ----------
        int x, z
            In range of 0 to 15
        y
            In range of -64 to 319

        Raises
        ------
        anvil.OutOfBoundCoordidnates
            If X, Y or Z are not in the proper range
        
        """
        if x < 0 or x > 15:
            raise OutOfBoundsCoordinates(f'X ({x!r}) must be in range of 0 to 15')
        if z < 0 or z > 15:
            raise OutOfBoundsCoordinates(f'Z ({z!r}) must be in range of 0 to 15')
        if y < -64 or y > 319:
            raise OutOfBoundsCoordinates(f'Y ({y!r}) must be in range of 0 to 255')
        section = self.sections[ (y + 64) // 16]
        if section is None:
            section = EmptySection( y // 16)
            self.add_section(section)
        section.set_block(block, x, y % 16, z)


    def set_biome(self, biome: Biome, x: int, y: int, z: int):
        """
        Sets biome at given coordinates
        
        Parameters
        ----------
        int x, z
            In range of 0 to 15
        y
            In range of -64 to 319

        Raises
        ------
        anvil.OutOfBoundCoordidnates
            If X, Y or Z are not in the proper range
        
        """
        if x < 0 or x > 15:
            raise OutOfBoundsCoordinates(f'X ({x!r}) must be in range of 0 to 15')
        if z < 0 or z > 15:
            raise OutOfBoundsCoordinates(f'Z ({z!r}) must be in range of 0 to 15')
        if y < -64 or y > 319:
            raise OutOfBoundsCoordinates(f'Y ({y!r}) must be in range of 0 to 255')
        section = self.sections[ (y + 64) // 16]
        if section is None:
            section = EmptySection( y // 16)
            self.add_section(section)
        section.set_biome(biome, x // 4, (y % 16) // 4, z // 4)

    def save(self) -> nbt.NBTFile:
        """
        Saves the chunk data to a :class:`NBTFile`

        Notes
        -----
        Does not contain most data a regular chunk would have,
        but minecraft stills accept it.
        """
        root = nbt.NBTFile()
        # 添加版本数据
        if self.version > 100:
            root['DataVersion'] = nbt.TAG_Int(value=self.version)
        # 获取基础数据
        try:
            last_update = self.data['LastUpdate'].value
        except:
            last_update = 0
        try:
            inhabited_time = self.data['InhabitedTime'].value
        except:
            inhabited_time = 0

        # 1.18-: 数据存储在Level标签下
        if self.version < 2844:

            # 创建 Level 标签
            level = nbt.TAG_Compound(name='Level')

            # 1.9-: 无数据版本的远古版本，只包含基础数据
            if self.version < 100:
                level.tags.extend([
                    nbt.TAG_List(name='Entities', type=nbt.TAG_Compound),
                    nbt.TAG_List(name='TileEntities', type=nbt.TAG_Compound),
                    nbt.TAG_Int(name='xPos', value=self.x),
                    nbt.TAG_Int(name='zPos', value=self.z),
                    nbt.TAG_Long(name='LastUpdate', value=last_update),
                ])

            # 1.9 - 1.13: 低版本基本字段，不包含光照和区块生成状态等高版本字段
            elif 100 <= self.version < 1451:
                level.tags.extend([
                    nbt.TAG_List(name='Entities', type=nbt.TAG_Compound),
                    nbt.TAG_List(name='TileEntities', type=nbt.TAG_Compound),
                    nbt.TAG_Int(name='xPos', value=self.x),
                    nbt.TAG_Int(name='zPos', value=self.z),
                    nbt.TAG_Long(name='LastUpdate', value=last_update),
                    nbt.TAG_Long(name='InhabitedTime', value=inhabited_time),
                    nbt.TAG_Byte(name='LightPopulated', value=0),
                ])
            # 1.13 - 1.18: 包含高版本基本字段，兼容低版本字段
            else:
                level.tags.extend([
                    nbt.TAG_List(name='Entities', type=nbt.TAG_Compound),
                    nbt.TAG_List(name='TileEntities', type=nbt.TAG_Compound),
                    nbt.TAG_List(name='LiquidTicks', type=nbt.TAG_Compound),
                    nbt.TAG_Int(name='xPos', value=self.x),
                    nbt.TAG_Int(name='zPos', value=self.z),
                    nbt.TAG_Long(name='LastUpdate', value=last_update),
                    nbt.TAG_Long(name='InhabitedTime', value=inhabited_time),
                    nbt.TAG_Byte(name='isLightOn', value=0),
                    nbt.TAG_String(name='Status', value=self.status),
                ])

            # 添加实体数据
            if self.entities is not None:
                level['Entities'] = self.entities

            # 添加方块实体
            if self.tile_entities is not None:
                level['TileEntities'] = self.tile_entities

            # 1.13-: 添加群系和HeightMap等低版本必须字段
            if self.version < 1451:
                try:
                    level['Biomes'] = self.data['Biomes']
                except:
                    pass
                try:
                    level['HeightMap'] = self.data['HeightMap']
                except:
                    pass
                try:
                    level['TerrainPopulated'] = self.data['TerrainPopulated']
                except:
                    pass

            # 添加区块数据
            sections = nbt.TAG_List(name='Sections', type=nbt.TAG_Compound)
            for y in sorted(self.sections):
                s = self.sections[y]
                if s:
                    sections.tags.append(s.save())
            level.tags.append(sections)
            root.tags.append(level)

        # 1.18+: 数据存储在根标签下
        else:
            root.tags.extend([
                nbt.TAG_List(name='Entities', type=nbt.TAG_Compound),
                nbt.TAG_List(name='block_entities', type=nbt.TAG_Compound),
                nbt.TAG_List(name='LiquidTicks', type=nbt.TAG_Compound),
                nbt.TAG_Int(name='xPos', value=self.x),
                nbt.TAG_Int(name='zPos', value=self.z),
                nbt.TAG_Long(name='LastUpdate', value=last_update),
                nbt.TAG_Long(name='InhabitedTime', value=inhabited_time),
                nbt.TAG_Byte(name='isLightOn', value=0),
                nbt.TAG_String(name='Status', value=self.status)
            ])
            # 如果有方块实体数据，则使用原始数据
            if self.tile_entities is not None:
                root['block_entities'] = self.tile_entities

            sections = nbt.TAG_List(name='sections', type=nbt.TAG_Compound)

            # 解除高度限制
            for y in sorted(self.sections):
                s = self.sections[y]
                if s:
                    sections.tags.append(s.save())
            root.tags.append(sections)

        return root
