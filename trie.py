import utils
import rlp
#import leveldb
from rlp.utils import decode_hex, ascii_chr, str_to_bytes
import sys

(
    NODE_TYPE_BLANK,
    NODE_TYPE_LEAF,
    NODE_TYPE_EXTENSION,
    NODE_TYPE_BRANCH
) = tuple(range(4))

BLANK_NODE = b''
BLANK_ROOT = utils.sha3rlp(b'')
bin_to_nibbles_cache = {}


NIBBLE_TERMINATOR = 16

def is_key_value_type(node_type):
    return node_type in [NODE_TYPE_LEAF,NODE_TYPE_EXTENSION]

def encode_optimized(item):
    if isinstance(item, bytes):
        if len(item) == 1 and ord(item) < 128:
            return item
        prefix = length_prefix(len(item), 128)
    else:
        item = b''.join([encode_optimized(x) for x in item])
        prefix = length_prefix(len(item), 192)
    return prefix + item

def length_prefix(length, offset):
    if length < 56:
        return chr(offset + length)
    else:
        length_string = utils.int_to_big_endian(length)
    return chr(offset + 56 - 1 + len(length_string)) + length_string

hti = {}
for i, c in enumerate(b'0123456789abcdef'):
    hti[c] = i
for i, c in enumerate('0123456789abcdef'):
    hti[c] = i


def bin_to_nibbles(s):
    return [hti[c] for c in utils.encode_hex(s)]


def nibbles_to_bin(nibbles):
    if any(x > 15 or x < 0 for x in nibbles):
        raise Exception("nibbles can only be [0,..15]")

    if len(nibbles) % 2:
        raise Exception("nibbles must be of even numbers")

    res = b''
    for i in range(0, len(nibbles), 2):
        res += ascii_chr(16 * nibbles[i] + nibbles[i + 1])
    return res

def with_terminator(nibbles):
    nibbles = nibbles[:]
    if not nibbles or nibbles[-1] != NIBBLE_TERMINATOR:
        nibbles.append(NIBBLE_TERMINATOR)
    return nibbles


def without_terminator(nibbles):
    nibbles = nibbles[:]
    if nibbles and nibbles[-1] == NIBBLE_TERMINATOR:
        del nibbles[-1]
    return nibbles


def adapt_terminator(nibbles, has_terminator):
    if has_terminator:
        return with_terminator(nibbles)
    else:
        return without_terminator(nibbles)


def pack_nibbles(nibbles):
    if nibbles[-1:] == [NIBBLE_TERMINATOR]:
        flags = 2
        nibbles = nibbles[:-1]
    else:
        flags = 0
    oddlen = len(nibbles) % 2
    flags |= oddlen
    if oddlen:
        nibbles = [flags] + nibbles
    else:
        nibbles = [flags, 0] + nibbles
    o = b''
    for i in range(0, len(nibbles), 2):
        o += ascii_chr(16 * nibbles[i] + nibbles[i + 1])
    return o


def unpack_to_nibbles(bindata):
    o = bin_to_nibbles(bindata)
    flags = o[0]
    if flags & 2:
        o.append(NIBBLE_TERMINATOR)
    if flags & 1 == 1:
        o = o[1:]
    else:
        o = o[2:]
    return o


def starts_with(full, part):
    if len(full) < len(part):
        return False
    return full[:len(part)] == part


class Trie(object):
    def __init__(self, db, root_hash=BLANK_ROOT):
        self.db = db  # Pass in a database object directly
        self.set_root_hash(root_hash)
        self.deletes = []

    @property
    def root_hash(self):
        return self._root_hash

    def get_root_hash(self):
        return self._root_hash

    def _update_root_hash(self):
        val = encode_optimized(self.root_node)
        key = utils.sha3(val)
        self.db.put(key, str_to_bytes(val))
        self._root_hash = key

    @root_hash.setter
    def root_hash(self, value):
        self.set_root_hash(value)

    def set_root_hash(self, root_hash):
        assert utils.is_string(root_hash)
        assert len(root_hash) in [0, 32]
        if root_hash == BLANK_ROOT:
            self.root_node = BLANK_NODE
            self._root_hash = BLANK_ROOT
            return
        self.root_node = self._decode_to_node(root_hash)
        self._root_hash = root_hash

    def clear(self):
        self._delete_child_storage(self.root_node)
        self._delete_node_storage(self.root_node)
        self.root_node = BLANK_NODE
        self._root_hash = BLANK_ROOT

    def _delete_child_storage(self, node):
        node_type = self._get_node_type(node)
        if node_type == NODE_TYPE_BRANCH:
            for item in node[:16]:
                self._delete_child_storage(self._decode_to_node(item))
        elif node_type == NODE_TYPE_EXTENSION:
            self._delete_child_storage(self._decode_to_node(node[1]))

    def _encode_node(self, node, put_in_db=True):
        if node == BLANK_NODE:
            return BLANK_NODE
        rlpnode = encode_optimized(node)
        if len(rlpnode) < 32:
            return node
        hashkey = utils.sha3(rlpnode)
        if put_in_db:
            self.db.put(hashkey, str_to_bytes(rlpnode))

        return hashkey

    def _decode_to_node(self, encoded):
        if encoded == BLANK_NODE:
            return BLANK_NODE
        if isinstance(encoded, list):
            return encoded
        o = rlp.decode(self.db.get(encoded))
        return o

    def _get_node_type(self, node):
        if node == BLANK_NODE:
            return NODE_TYPE_BLANK

        if len(node) == 2:
            nibbles = unpack_to_nibbles(node[0])
            has_terminator = (nibbles and nibbles[-1] == NIBBLE_TERMINATOR)
            return NODE_TYPE_LEAF if has_terminator \
                else NODE_TYPE_EXTENSION
        if len(node) == 17:
            return NODE_TYPE_BRANCH

    def _get(self, node, key):
        node_type = self._get_node_type(node)

        if node_type == NODE_TYPE_BLANK:
            return BLANK_NODE

        if node_type == NODE_TYPE_BRANCH:
            if not key:
                return node[-1]
            sub_node = self._decode_to_node(node[key[0]])
            return self._get(sub_node, key[1:])

        curr_key = without_terminator(unpack_to_nibbles(node[0]))
        if node_type == NODE_TYPE_LEAF:
            return node[1] if key == curr_key else BLANK_NODE

        if node_type == NODE_TYPE_EXTENSION:
            if starts_with(key, curr_key):
                sub_node = self._decode_to_node(node[1])
                return self._get(sub_node, key[len(curr_key):])
            else:
                return BLANK_NODE

    def _update(self, node, key, value):
        node_type = self._get_node_type(node)

        if node_type == NODE_TYPE_BLANK:
            return [pack_nibbles(with_terminator(key)), value]

        elif node_type == NODE_TYPE_BRANCH:
            if not key:
                node[-1] = value
            else:
                new_node = self._update_and_delete_storage(
                    self._decode_to_node(node[key[0]]),
                    key[1:], value)
                node[key[0]] = self._encode_node(new_node)
            return node

        elif is_key_value_type(node_type):
            return self._update_kv_node(node, key, value)

    def _update_and_delete_storage(self, node, key, value):
        old_node = node[:]
        new_node = self._update(node, key, value)
        if old_node != new_node:
            self._delete_node_storage(old_node)
        return new_node

    def _update_kv_node(self, node, key, value):
        node_type = self._get_node_type(node)
        curr_key = without_terminator(unpack_to_nibbles(node[0]))
        is_inner = node_type == NODE_TYPE_EXTENSION


        prefix_length = 0
        for i in range(min(len(curr_key), len(key))):
            if key[i] != curr_key[i]:
                break
            prefix_length = i + 1

        remain_key = key[prefix_length:]
        remain_curr_key = curr_key[prefix_length:]

        if remain_key == [] == remain_curr_key:
            if not is_inner:
                return [node[0], value]
            new_node = self._update_and_delete_storage(
                self._decode_to_node(node[1]), remain_key, value)

        elif remain_curr_key == []:
            if is_inner:
                new_node = self._update_and_delete_storage(
                    self._decode_to_node(node[1]), remain_key, value)
            else:
                new_node = [BLANK_NODE] * 17
                new_node[-1] = node[1]
                new_node[remain_key[0]] = self._encode_node([
                    pack_nibbles(with_terminator(remain_key[1:])),
                    value
                ])
        else:
            new_node = [BLANK_NODE] * 17
            if len(remain_curr_key) == 1 and is_inner:
                new_node[remain_curr_key[0]] = node[1]
            else:
                new_node[remain_curr_key[0]] = self._encode_node([
                    pack_nibbles(
                        adapt_terminator(remain_curr_key[1:], not is_inner)
                    ),
                    node[1]
                ])

            if remain_key == []:
                new_node[-1] = value
            else:
                new_node[remain_key[0]] = self._encode_node([
                    pack_nibbles(with_terminator(remain_key[1:])), value
                ])

        if prefix_length:
            return [pack_nibbles(curr_key[:prefix_length]),
                    self._encode_node(new_node)]
        else:
            return new_node

    def _getany(self, node, reverse=False, path=[]):
        node_type = self._get_node_type(node)
        if node_type == NODE_TYPE_BLANK:
            return None
        if node_type == NODE_TYPE_BRANCH:
            if node[16] and not reverse:
                return [16]
            scan_range = list(range(16))
            if reverse:
                scan_range.reverse()
            for i in scan_range:
                o = self._getany(
                    self._decode_to_node(
                        node[i]),
                    reverse=reverse,
                    path=path + [i])
                if o is not None:
                    return [i] + o
            if node[16] and reverse:
                return [16]
            return None
        curr_key = without_terminator(unpack_to_nibbles(node[0]))
        if node_type == NODE_TYPE_LEAF:
            return curr_key

        if node_type == NODE_TYPE_EXTENSION:
            curr_key = without_terminator(unpack_to_nibbles(node[0]))
            sub_node = self._decode_to_node(node[1])
            return curr_key + \
                   self._getany(sub_node, reverse=reverse, path=path + curr_key)

    def _split(self, node, key):
        node_type = self._get_node_type(node)
        if node_type == NODE_TYPE_BLANK:
            return BLANK_NODE, BLANK_NODE
        elif not key:
            return BLANK_NODE, node
        elif node_type == NODE_TYPE_BRANCH:
            b1 = node[:key[0]]
            b1 += [''] * (17 - len(b1))
            b2 = node[key[0] + 1:]
            b2 = [''] * (17 - len(b2)) + b2
            b1[16], b2[16] = b2[16], b1[16]
            sub = self._decode_to_node(node[key[0]])
            sub1, sub2 = self._split(sub, key[1:])
            b1[key[0]] = self._encode_node(sub1) if sub1 else ''
            b2[key[0]] = self._encode_node(sub2) if sub2 else ''
            return self._normalize_branch_node(b1) if len([x for x in b1 if x]) else BLANK_NODE, \
                   self._normalize_branch_node(b2) if len(
                       [x for x in b2 if x]) else BLANK_NODE

        descend_key = without_terminator(unpack_to_nibbles(node[0]))
        if node_type == NODE_TYPE_LEAF:
            if descend_key < key:
                return node, BLANK_NODE
            else:
                return BLANK_NODE, node
        elif node_type == NODE_TYPE_EXTENSION:
            sub_node = self._decode_to_node(node[1])
            sub_key = key[len(descend_key):]
            if starts_with(key, descend_key):
                sub1, sub2 = self._split(sub_node, sub_key)
                subtype1 = self._get_node_type(sub1)
                subtype2 = self._get_node_type(sub2)
                if not sub1:
                    o1 = BLANK_NODE
                elif subtype1 in (NODE_TYPE_LEAF, NODE_TYPE_EXTENSION):
                    new_key = key[:len(descend_key)] + \
                              unpack_to_nibbles(sub1[0])
                    o1 = [pack_nibbles(new_key), sub1[1]]
                else:
                    o1 = [pack_nibbles(key[:len(descend_key)]),
                          self._encode_node(sub1)]
                if not sub2:
                    o2 = BLANK_NODE
                elif subtype2 in (NODE_TYPE_LEAF, NODE_TYPE_EXTENSION):
                    new_key = key[:len(descend_key)] + \
                              unpack_to_nibbles(sub2[0])
                    o2 = [pack_nibbles(new_key), sub2[1]]
                else:
                    o2 = [pack_nibbles(key[:len(descend_key)]),
                          self._encode_node(sub2)]
                return o1, o2
            elif descend_key < key[:len(descend_key)]:
                return node, BLANK_NODE
            elif descend_key > key[:len(descend_key)]:
                return BLANK_NODE, node
            else:
                return BLANK_NODE, BLANK_NODE

    def split(self, key):
        key = bin_to_nibbles(key)
        r1, r2 = self._split(self.root_node, key)
        t1, t2 = Trie(self.db), Trie(self.db)
        t1.root_node, t2.root_node = r1, r2
        return t1, t2

    def _merge(self, node1, node2):
        node_type1 = self._get_node_type(node1)
        node_type2 = self._get_node_type(node2)
        if not node1:
            return node2
        if not node2:
            return node1
        if node_type1 != NODE_TYPE_BRANCH and node_type2 != NODE_TYPE_BRANCH:
            descend_key1 = unpack_to_nibbles(node1[0])
            descend_key2 = unpack_to_nibbles(node2[0])
            prefix_length = 0
            for i in range(min(len(descend_key1), len(descend_key2))):
                if descend_key1[i] != descend_key2[i]:
                    break
                prefix_length = i + 1
            if prefix_length:
                sub1 = self._decode_to_node(
                    node1[1]) if node_type1 == NODE_TYPE_EXTENSION else node1[1]
                new_sub1 = [
                    pack_nibbles(descend_key1[prefix_length:]),
                    sub1
                ] if descend_key1[prefix_length:] else sub1
                sub2 = self._decode_to_node(
                    node2[1]) if node_type2 == NODE_TYPE_EXTENSION else node2[1]
                new_sub2 = [
                    pack_nibbles(descend_key2[prefix_length:]),
                    sub2
                ] if descend_key2[prefix_length:] else sub2
                return [pack_nibbles(descend_key1[:prefix_length]),
                        self._encode_node(self._merge(new_sub1, new_sub2))]

        nodes = [[node1], [node2]]
        for (node, node_type) in zip(nodes, [node_type1, node_type2]):
            if node_type != NODE_TYPE_BRANCH:
                new_node = [BLANK_NODE] * 17
                curr_key = unpack_to_nibbles(node[0][0])
                new_node[curr_key[0]] = self._encode_node([
                    pack_nibbles(curr_key[1:]),
                    node[0][1]
                ]) if curr_key[0] < 16 and curr_key[1:] else node[0][1]
                node[0] = new_node
        node1, node2 = nodes[0][0], nodes[1][0]
        assert len([i for i in range(17) if node1[i] and node2[i]]) <= 1
        new_node = [
            self._encode_node(
                self._merge(
                    self._decode_to_node(
                        node1[i]), self._decode_to_node(
                        node2[i]))) if node1[i] and node2[i] else node1[i] or node2[i] for i in range(17)]
        return new_node

    @classmethod
    def unsafe_merge(cls, trie1, trie2):
        t = Trie(trie1.db)
        t.root_node = t._merge(trie1.root_node, trie2.root_node)
        return t

    def _iter(self, node, key, reverse=False, path=[]):
        node_type = self._get_node_type(node)

        if node_type == NODE_TYPE_BLANK:
            return None

        elif node_type == NODE_TYPE_BRANCH:
            if len(key):
                sub_node = self._decode_to_node(node[key[0]])
                o = self._iter(sub_node, key[1:], reverse, path + [key[0]])
                if o is not None:
                    return [key[0]] + o
            if reverse:
                scan_range = reversed(list(range(key[0] if len(key) else 0)))
            else:
                scan_range = list(range(key[0] + 1 if len(key) else 0, 16))
            for i in scan_range:
                sub_node = self._decode_to_node(node[i])
                o = self._getany(sub_node, reverse, path + [i])
                if o is not None:
                    return [i] + o
            if reverse and key and node[16]:
                return [16]
            return None

        descend_key = without_terminator(unpack_to_nibbles(node[0]))
        if node_type == NODE_TYPE_LEAF:
            if reverse:
                return descend_key if descend_key < key else None
            else:
                return descend_key if descend_key > key else None

        if node_type == NODE_TYPE_EXTENSION:
            sub_node = self._decode_to_node(node[1])
            sub_key = key[len(descend_key):]
            if starts_with(key, descend_key):
                o = self._iter(sub_node, sub_key, reverse, path + descend_key)
            elif descend_key > key[:len(descend_key)] and not reverse:
                o = self._getany(sub_node, False, path + descend_key)
            elif descend_key < key[:len(descend_key)] and reverse:
                o = self._getany(sub_node, True, path + descend_key)
            else:
                o = None
            return descend_key + o if o else None

    def next(self, key):
        key = bin_to_nibbles(key)
        o = self._iter(self.root_node, key)
        return nibbles_to_bin(without_terminator(o)) if o else None

    def prev(self, key):
        key = bin_to_nibbles(key)
        o = self._iter(self.root_node, key, reverse=True)
        return nibbles_to_bin(without_terminator(o)) if o else None

    def _delete_node_storage(self, node):
        if node == BLANK_NODE:
            return
        encoded = self._encode_node(node, put_in_db=False)

        if len(encoded) < 32:
            return
        self.deletes.append(encoded)

    def _delete(self, node, key):
        node_type = self._get_node_type(node)
        if node_type == NODE_TYPE_BLANK:
            return BLANK_NODE

        if node_type == NODE_TYPE_BRANCH:
            return self._delete_branch_node(node, key)

        if is_key_value_type(node_type):
            return self._delete_kv_node(node, key)

    def _normalize_branch_node(self, node):

        not_blank_items_count = sum(1 for x in range(17) if node[x])
        assert not_blank_items_count >= 1

        if not_blank_items_count > 1:
            return node

        not_blank_index = [i for i, item in enumerate(node) if item][0]

        if not_blank_index == 16:
            return [pack_nibbles(with_terminator([])), node[16]]

        sub_node = self._decode_to_node(node[not_blank_index])
        sub_node_type = self._get_node_type(sub_node)

        if is_key_value_type(sub_node_type):
            new_key = [not_blank_index] + \
                      unpack_to_nibbles(sub_node[0])
            return [pack_nibbles(new_key), sub_node[1]]
        if sub_node_type == NODE_TYPE_BRANCH:
            return [pack_nibbles([not_blank_index]),
                    self._encode_node(sub_node)]
        assert False

    def _delete_and_delete_storage(self, node, key):
        old_node = node[:]
        new_node = self._delete(node, key)
        if old_node != new_node:
            self._delete_node_storage(old_node)
        return new_node

    def _delete_branch_node(self, node, key):
        if not key:
            node[-1] = BLANK_NODE
            return self._normalize_branch_node(node)

        encoded_new_sub_node = self._encode_node(
            self._delete_and_delete_storage(
                self._decode_to_node(node[key[0]]), key[1:])
        )

        if encoded_new_sub_node == node[key[0]]:
            return node

        node[key[0]] = encoded_new_sub_node
        if encoded_new_sub_node == BLANK_NODE:
            return self._normalize_branch_node(node)

        return node

    def _delete_kv_node(self, node, key):
        node_type = self._get_node_type(node)
        assert is_key_value_type(node_type)
        curr_key = without_terminator(unpack_to_nibbles(node[0]))

        if not starts_with(key, curr_key):
            return node

        if node_type == NODE_TYPE_LEAF:
            return BLANK_NODE if key == curr_key else node

        new_sub_node = self._delete_and_delete_storage(
            self._decode_to_node(node[1]), key[len(curr_key):])

        if self._encode_node(new_sub_node) == node[1]:
            return node

        if new_sub_node == BLANK_NODE:
            return BLANK_NODE

        new_sub_node_type = self._get_node_type(new_sub_node)

        if is_key_value_type(new_sub_node_type):
            new_key = curr_key + unpack_to_nibbles(new_sub_node[0])
            return [pack_nibbles(new_key), new_sub_node[1]]

        if new_sub_node_type == NODE_TYPE_BRANCH:
            return [pack_nibbles(curr_key), self._encode_node(new_sub_node)]

        assert False

    def delete(self, key):
        if not utils.is_string(key):
            raise Exception("Key must be string")

        if len(key) > 32:
            raise Exception("Max key length is 32")

        self.root_node = self._delete_and_delete_storage(
            self.root_node,
            bin_to_nibbles(utils.to_string(key)))
        self._update_root_hash()

    def _get_size(self, node):
        if node == BLANK_NODE:
            return 0

        node_type = self._get_node_type(node)

        if is_key_value_type(node_type):
            value_is_node = node_type == NODE_TYPE_EXTENSION
            if value_is_node:
                return self._get_size(self._decode_to_node(node[1]))
            else:
                return 1
        elif node_type == NODE_TYPE_BRANCH:
            sizes = [self._get_size(self._decode_to_node(node[x]))
                     for x in range(16)]
            sizes = sizes + [1 if node[-1] else 0]
            return sum(sizes)

    def _iter_branch(self, node):
        if node == BLANK_NODE:
            raise StopIteration

        node_type = self._get_node_type(node)

        if is_key_value_type(node_type):
            nibbles = without_terminator(unpack_to_nibbles(node[0]))
            key = b'+'.join([utils.to_string(x) for x in nibbles])
            if node_type == NODE_TYPE_EXTENSION:
                sub_tree = self._iter_branch(self._decode_to_node(node[1]))
            else:
                sub_tree = [(utils.to_string(NIBBLE_TERMINATOR), node[1])]

            for sub_key, sub_value in sub_tree:
                full_key = (key + b'+' + sub_key).strip(b'+')
                yield (full_key, sub_value)

        elif node_type == NODE_TYPE_BRANCH:
            for i in range(16):
                sub_tree = self._iter_branch(self._decode_to_node(node[i]))
                for sub_key, sub_value in sub_tree:
                    full_key = (
                        str_to_bytes(
                            str(i)) +
                        b'+' +
                        sub_key).strip(b'+')
                    yield (full_key, sub_value)
            if node[16]:
                yield (utils.to_string(NIBBLE_TERMINATOR), node[-1])

    def iter_branch(self):
        for key_str, value in self._iter_branch(self.root_node):
            if key_str:
                nibbles = [int(x) for x in key_str.split(b'+')]
            else:
                nibbles = []
            key = nibbles_to_bin(without_terminator(nibbles))
            yield key, value

    def _to_dict(self, node):
        if node == BLANK_NODE:
            return {}

        node_type = self._get_node_type(node)

        if is_key_value_type(node_type):
            nibbles = without_terminator(unpack_to_nibbles(node[0]))
            key = b'+'.join([utils.to_string(x) for x in nibbles])
            if node_type == NODE_TYPE_EXTENSION:
                sub_dict = self._to_dict(self._decode_to_node(node[1]))
            else:
                sub_dict = {utils.to_string(NIBBLE_TERMINATOR): node[1]}
            res = {}
            for sub_key, sub_value in sub_dict.items():
                full_key = (key + b'+' + sub_key).strip(b'+')
                res[full_key] = sub_value
            return res

        elif node_type == NODE_TYPE_BRANCH:
            res = {}
            for i in range(16):
                sub_dict = self._to_dict(self._decode_to_node(node[i]))

                for sub_key, sub_value in sub_dict.items():
                    full_key = (
                        str_to_bytes(
                            str(i)) +
                        b'+' +
                        sub_key).strip(b'+')
                    res[full_key] = sub_value

            if node[16]:
                res[utils.to_string(NIBBLE_TERMINATOR)] = node[-1]
            return res

    def to_dict(self):
        d = self._to_dict(self.root_node)
        res = {}
        for key_str, value in d.items():
            if key_str:
                nibbles = [int(x) for x in key_str.split(b'+')]
            else:
                nibbles = []
            key = nibbles_to_bin(without_terminator(nibbles))
            res[key] = value
        return res

    def get(self, key):
        return self._get(self.root_node, bin_to_nibbles(utils.to_string(key)))

    def __len__(self):
        return self._get_size(self.root_node)

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        return self.update(key, value)

    def __delitem__(self, key):
        return self.delete(key)

    def __iter__(self):
        return iter(self.to_dict())

    def __contains__(self, key):
        return self.get(key) != BLANK_NODE

    def update(self, key, value):
        if not utils.is_string(key):
            raise Exception("Key must be string")

        if not utils.is_string(value):
            raise Exception("Value must be string")

        self.root_node = self._update_and_delete_storage(
            self.root_node,
            bin_to_nibbles(utils.to_string(key)),
            utils.to_string(value))
        self._update_root_hash()

    def root_hash_valid(self):
        if self.root_hash == BLANK_ROOT:
            return True
        return self.root_hash in self.db
