import zlib
from io import BytesIO
from typing import Tuple, Union, BinaryIO

from . import nbt
from .chunk import Chunk
from .errors import GZipChunkData, ChunkNotFound


class Region:
    """
    Read-only region

    Attributes
    ----------
    data: :class:`bytes`
        Region file (``.mca``) as bytes
    """
    __slots__ = ('data',)
    def __init__(self, data: bytes):
        """Makes a Region object from data, which is the region file content"""
        self.data = data

    @staticmethod
    def header_offset(chunk_x: int, chunk_z: int) -> int:
        """
        Returns the byte offset for given chunk in the header
        
        Parameters
        ----------
        chunk_x
            Chunk's X value
        chunk_z
            Chunk's Z value
        """
        return 4 * (chunk_x % 32 + chunk_z % 32 * 32)

    def chunk_location(self, chunk_x: int, chunk_z: int) -> Tuple[int, int]:
        """
        Returns the chunk offset in the 4KiB sectors from the start of the file,
        and the length of the chunk in sectors of 4KiB

        Will return ``(0, 0)`` if chunk hasn't been generated yet

        Parameters
        ----------
        chunk_x
            Chunk's X value
        chunk_z
            Chunk's Z value
        """
        b_off = self.header_offset(chunk_x, chunk_z)
        off = int.from_bytes(self.data[b_off : b_off + 3], byteorder='big')
        sectors = self.data[b_off + 3]
        return off, sectors



    def chunk_data(self, chunk_x: int, chunk_z: int) -> nbt.NBTFile:
        """
        Returns the NBT data for a chunk
        return: 区块NBT数据 nbt.NBTFile
                None: 区块为空
                False: 区块存储在外部.mcc文件中
        """
        off = self.chunk_location(chunk_x, chunk_z)

        # 区块不存在
        if off == (0, 0):
            return None

        off = off[0] * 4096

        length = int.from_bytes(self.data[off:off + 4], byteorder='big')
        compression = self.data[off + 4]

        # 区块存储在外部.mcc文件中
        if length == 1 or (compression & 0x80):
            return False

        # 不支持gzip
        if compression == 1:
            return None
            # raise GZipChunkData('GZip is not supported')

        compressed_data = self.data[off + 5: off + 5 + length - 1]
        return nbt.NBTFile(buffer=BytesIO(zlib.decompress(compressed_data)))


    def get_chunk(self, chunk_x: int, chunk_z: int) -> Chunk:
        """
        Returns the chunk at given coordinates,
        same as doing ``Chunk.from_region(region, chunk_x, chunk_z)``

        Parameters
        ----------
        chunk_x
            Chunk's X value
        chunk_z
            Chunk's Z value
        
        
        :rtype: :class:`anvil.Chunk`
        """
        nbt_data = self.chunk_data(chunk_x, chunk_z)
        # 判断无效区块
        if not nbt_data:
            return nbt_data

        # 包装并返回区块对象
        return Chunk(nbt_data)

    @classmethod
    def from_file(cls, file: Union[str, BinaryIO]):
        """
        Creates a new region with the data from reading the given file

        Parameters
        ----------
        file
            Either a file path or a file object
        """
        if isinstance(file, str):
            with open(file, 'rb') as f:
                return cls(data=f.read())
        else:
            return cls(data=file.read())
