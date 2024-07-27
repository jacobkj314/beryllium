import React, {useState} from 'react';
import type { FormProps } from 'antd';
import { Button, Form, Input, Typography, Alert, Space } from 'antd';

export default function Signup() {

const [disableButton, setDisableButton] = useState<boolean>(true);

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


return(
  <div style={{ textAlign:'center', marginTop:'50px'}}>
        <Title style={{display:'block'}}>Sign up</Title>

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

        <Form.Item wrapperCol={{ offset: 5, span:20 }}>
          <Alert
            message="Info Text"
            description={<p>By signing up, you agree that the owners/admins of this Beryllium instance may permanently retain your username and a cryptographic hash of your password. In the future, this Beryllium instance may retain a list of users whose images you would like to view and/or a list of users whom you permit to view your images. No other data shall be maintained permanently. For more details, visit <a href="https://github.com/jacobkj314/beryllium">https://github.com/jacobkj314/beryllium</a></p>}
            type="info"
            action={
              <Space direction="vertical">
                <Button size="small" type="primary" onClick={() => setDisableButton(false)}>
                  Accept
                </Button>
                <Button size="small" danger ghost onClick={() => setDisableButton(true)}>
                  Decline
                </Button>
              </Space>
            }
          />
        </Form.Item>
        
        <Form.Item wrapperCol={{ offset: 8, span:8 }}>
          <Button type="primary" htmlType="submit" disabled={disableButton}>
            Sign up
          </Button>
        </Form.Item>
        </Form>

        <Link style={{display:'block'}} href="/login">Already have an account? Sign in here!</Link>
  </div>
)}