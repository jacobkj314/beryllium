import React from 'react';
import type { FormProps } from 'antd';
import { Button, Form, Input, Typography } from 'antd';

export default function Signup() {

const { Title, Link } = Typography;

type FieldType = {
  username?: string;
  password?: string;
  remember?: string;
};

const onFinish: FormProps<FieldType>['onFinish'] = (values) => {
  console.log('Success:', values);
};

const onFinishFailed: FormProps<FieldType>['onFinishFailed'] = (errorInfo) => {
  console.log('Failed:', errorInfo);
};

return (
  <div style={{ textAlign:'center', marginTop:'50px'}}>
        <Title style={{display:'block'}}>Login</Title>

        <Form
          name="basic"
          labelCol={{ span: 8 }}
          wrapperCol={{ span: 16 }}
          style={{ display:'inline-block', maxWidth: 600 }}
          initialValues={{ remember: true }}
          onFinish={onFinish}
          onFinishFailed={onFinishFailed}
          autoComplete="off"
        >
        <Form.Item<FieldType>
          label="Username"
          name="username"
          rules={[{ required: true, message: 'Please input your username!' }]}
        >
          <Input />
        </Form.Item>

        <Form.Item<FieldType>
          label="Password"
          name="password"
          rules={[{ required: true, message: 'Please input your password!' }]}
        >
          <Input.Password />
        </Form.Item>

        <Form.Item wrapperCol={{ offset: 8, span:8 }}>
          <Button type="primary" htmlType="submit">
            Login
          </Button>
        </Form.Item>
        </Form>

        <Link style={{display:'block'}} href="/signup">No account? Sign up here!</Link>
  </div>
)}