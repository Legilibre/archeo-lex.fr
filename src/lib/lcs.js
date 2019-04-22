function lcs(text_a, text_b) {

	if( !text_a || !text_b ) {
		return { length: 0, indexes: [] }
	}

	const n = text_a.length,
	      m = text_b.length

	let length = 0,
	    indexes = [],
	    matrix = new Array(2*m),
	    i, j, newIndex

	for( i=0; i<n; i++ ) {
		for( j=0; j<m; j++ ) {
			if( text_a[i] === text_b[j] ) {
				if( i === 0 || j === 0 ) {
					matrix[i%2+2*j] = 1
				} else {
					matrix[i%2+2*j] = matrix[(i-1)%2+2*(j-1)] + 1
				}
				newIndex = [i - matrix[i%2+2*j] + 1, j - matrix[i%2+2*j] + 1]
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
