import { useState, useEffect } from 'react';


import { TestApi } from '../rest/__APP_NAME__/apis/TestApi'
const test = new TestApi();



const RestTest = () => {
  const [result, setResult] = useState<any>(null);
  useEffect(() => {
    test.ping().then((r) => setResult(r), () => setResult("API error"));
  }, []);


  return result ? <p>Backend answered: {result} </p> : <p>Backend did not answer</p>
}

export default RestTest;