import React from "react";
import {Button, Form, Input, Select} from "antd";
import {Aspect, Entity} from "../../services/metaModelService";
import TextArea from "antd/es/input/TextArea";


export interface Props {
    aspects: Aspect[];
    entity: Partial<Entity>;
    onChange: (e: Partial<Entity>) => void;
    onSubmit: (e: Entity) => void;
}

const EntityInput = ({aspects, entity, onChange, onSubmit}: Props) => {
    return (
        <Form>
            <Form.Item>New Entity</Form.Item>
            <Form.Item label={"name"}>
                <Input value={entity.name} onChange={(e) => {
                    onChange({
                        ...entity,
                        name: e.target.value
                    })
                }}/>
            </Form.Item>
            <Form.Item label={"description"}>
                <TextArea value={entity.description} onChange={(e) => {
                    onChange({
                        ...entity,
                        description: e.target.value
                    })
                }}/>
            </Form.Item>
            <Form.Item label={"aspect"}>
                <Select
                    onChange={(_, option) => {
                        if(Array.isArray(option)) {
                            throw Error();
                        }
                        onChange({
                            ...entity,
                            aspect: option.aspect
                        })
                    }}
                >
                    {aspects.map(a => <Select.Option value={a.name} aspect={a} key={a.name}>{a.name}</Select.Option>)}
                </Select>
            </Form.Item>
            <Form.Item>
                <Button
                    type={"primary"}
                    onClick={() => {
                        if(!entity.description) return;
                        if(!entity.aspect) return;
                        if(!entity.name) return;
                        onSubmit({
                            name: entity.name,
                            aspect: entity.aspect,
                            description: entity.description,
                            position: {
                                x: Math.random() * 150,
                                y: Math.random() * 150
                            }
                        });
                    }}
                >
                    Create
                </Button>
            </Form.Item>
        </Form>
    );
}

export default EntityInput;