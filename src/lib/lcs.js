function lcs(text_a, text_b, alo, ahi, blo, bhi) {

	alo = alo >= 0 ? alo : 0
	blo = blo >= 0 ? blo : 0
	ahi = ahi <= text_a.length ? ahi : text_a.length
	bhi = bhi <= text_b.length ? bhi : text_b.length

	if( alo >= ahi || blo >= bhi ) {
		return { length: 0, indexes: [] }
	}

	const n = ahi - alo,
	      m = bhi - blo

	let length = 0,
	    indexes = [],
	    matrix = new Array(2*m),
	    i, j, newIndex

	for( i=0; i<n; i++ ) {
		for( j=0; j<m; j++ ) {
			if( text_a[alo+i] === text_b[blo+j] ) {
				if( i === 0 || j === 0 ) {
					matrix[i%2+2*j] = 1
				} else {
					matrix[i%2+2*j] = matrix[(i-1)%2+2*(j-1)] + 1
				}
				newIndex = [alo + i - matrix[i%2+2*j] + 1, blo + j - matrix[i%2+2*j] + 1]
				if( matrix[i%2+2*j] > length ) {
					length = matrix[i%2+2*j]
					indexes = [newIndex]
				} else if( matrix[i%2+2*j] === length ) {
					indexes.push(newIndex)
				}
			} else {
				matrix[i%2+2*j] = 0
			}
		}
	}

	return { length, indexes }
}

export { lcs }
