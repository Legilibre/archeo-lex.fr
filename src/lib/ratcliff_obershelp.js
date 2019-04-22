import { lcs } from './lcs';

function ratcliff_obershelp(text_a, text_b, keeplcs) {

	const n = text_a.length,
	      m = text_b.length

	let queue = [ [ 0, n, 0, m ] ],
	    matching_blocks = [],
	    non_adjacent = [],
	    counter = 0,
	    alo, ahi, blo, bhi,
	    indexes, i, j, k, l,
	    i1, j1, k1, i2, j2, k2

	while( queue.length > 0 ) {

		[ alo, ahi, blo, bhi ] = queue.pop()
		let { length: k, indexes } = lcs(text_a, text_b, alo, ahi, blo, bhi)
		if( k === 0 ) {
			continue
		}
		i = indexes[0][0]
		j = indexes[0][1]
		if( keeplcs ) {
			let { i: i3, j: j3, k: k3, l } = keeplcs( i, j, k, indexes[0], text_a, text_b, n, m )
			if( l === false || k3 <= 0 ) {
				continue
			}
			i = i3
			j = j3
			k = k3
		}
		matching_blocks.push( [ i, j, k ] )
		if( alo < i && blo < j ) {
			queue.push( [ alo, i, blo, j ] )
		}
		if( i + k < ahi && j + k < bhi ) {
			queue.push( [ i + k, ahi, j + k, bhi ] )
		}
		counter++
		if( counter > 100 ) {
			break
		}
	}

	matching_blocks.sort((a, b) => {
		for( let i=0; i<4; i++ ) {
			if( a[i] === b[i] ) {
				continue
			}
			return a[i] < b[i] ? -1 : 1
		}
	})

	i1 = 0, j1 = 0, k1 = 0
	for( i=0; i<matching_blocks.length; i++ ) {
		[ i2, j2, k2 ] = matching_blocks[i]
		if( i1 + k1 === i2 && j1 + k1 === j2 ) {
			k1 += k2
		} else {
			if( k1 ) {
				non_adjacent.push( [ i1, j1, k1 ] )
			}
			i1 = i2
			j1 = j2
			k1 = k2
		}
	}
	if( k1 ) {
		non_adjacent.push( [ i1, j1, k1 ] )
	}
	non_adjacent.push( [ n, m, 0 ] )

	return non_adjacent
}

export { ratcliff_obershelp }
