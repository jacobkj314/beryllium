import React from 'react';
import { Typography, Button, Space } from 'antd';

export default function CustomHeader() {

  const { Title } = Typography;

  return (
    <div style={{textAlign:'center'}}>
      <Space size={'large'}>
        <Title  style={{display:'inline-block'}}>BERYLLIUM</Title>
        <Button  style={{display:'inline-block'}} type="primary">Logout</Button>
      </Space>
    </div>
)}