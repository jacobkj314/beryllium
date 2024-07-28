import React from 'react';
import CustomHeader from './CustomHeader';
import { Image, Typography, Space, List, Form, Input, Button } from 'antd';

export default function Main() {

  const { Title } = Typography;

  const data = [
    'Comments are ',
    'To go here',
    'And populate this area',
    'with some data'
  ];

  const onFinish = (values : any) => {
    console.log('Success:', values);
  };
  
  const onFinishFailed = (errorInfo : any) => {
    console.log('Failed:', errorInfo);
  };

  return (
  <div>
    <CustomHeader />
    
    <div>
      <Space size={'small'}>
        <Title level={3} style={{display: 'inline-block'}}>Username goes here</Title>
        <Title level={3} style={{display: 'inline-block'}}>Date and tim go here</Title>
      </Space>
    </div>

    <Image
      width={200}
      src="https://zos.alipayobjects.com/rmsportal/jkjgkEfvpUPVyRjUImniVslZfWPnJuuZ.png"
    />
    <Image
      width={200}
      src="https://zos.alipayobjects.com/rmsportal/jkjgkEfvpUPVyRjUImniVslZfWPnJuuZ.png"
    />

    <div>
      <List
        size="large"
        style={{maxWidth:'1000px'}}
        header={<Title level={4}>Comments</Title>}
        dataSource={data}
        renderItem={(item) => <List.Item>{item}</List.Item>}
      />
      <Form
          name="basic"
          labelCol={{ span: 8 }}
          wrapperCol={{ span: 16 }}
          style={{ display:'inline-block', maxWidth:'100%'}}
          initialValues={{ remember: true }}
          onFinish={onFinish}
          onFinishFailed={onFinishFailed}
          autoComplete="off"
        >

          <Form.Item
            name="postcomment"
            style={{display: 'inline-block', marginTop:'10px'}}
            wrapperCol={{span:20}}
          >
            <Input />
          </Form.Item>

          <Form.Item style={{display: 'inline-block', marginTop:'10px'}}>
            <Button type="primary" htmlType="submit">
              Post Comment
            </Button>
          </Form.Item>
        </Form>
    </div>
  </div>
)}