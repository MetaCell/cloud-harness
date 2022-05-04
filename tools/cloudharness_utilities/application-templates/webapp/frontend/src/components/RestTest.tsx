import React, { useState, useEffect } from 'react';


import { TestApi } from '../rest/api'
const test = new TestApi();

const RestTest = () => {
  const [result, setResult] = useState(null);
  useEffect(() => {
    test.ping().then(r => setResult(r));
  }, []);
    

  return result && <p>Backend answered: { result.data } </p>
}

export default RestTest;